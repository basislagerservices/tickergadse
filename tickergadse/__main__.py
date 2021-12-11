#
# Copyright 2021 Basislager Services
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

"""Crawler for the Seuchenticker Basislager."""

import argparse
import asyncio
import contextlib
import datetime as dt
import json
import logging
import os
import sys
import tempfile
import time
from typing import Any, ContextManager, Optional

from . import git
from .gadse import TickerGadse


DESCRIPTION = (
    "Continuously update the postcount and other stats of a live ticker. "
    "Results are committed and pushed to a Git repository. "
    "The crawler creates a ranking.json file, which is saved in the directory "
    "given with the --git-subdir argument."
)

TICKER_ID = 2000130527798

logger = logging.getLogger(__name__)


async def commit_ranking(
    gadse: TickerGadse,
    repopath: str,
    subdir: str,
    message: str,
) -> None:
    """Write the ranking to the repository and commit it."""
    result_dir = os.path.join(repopath, subdir)
    result_path = os.path.join(result_dir, "ranking.json")
    os.makedirs(result_dir, exist_ok=True)

    # Create the desired ranking.json structure.
    ranking: dict[str, Any] = dict()
    ranking["date"] = gadse.last_update.strftime("%d.%m.%Y - %H:%M (UTC)")
    ranking["users"] = [{"name": k, "postings": v} for k, v in gadse.ranking.items()]
    with open(result_path, "w") as fp:
        json.dump(ranking, fp, indent=4, sort_keys=True)

    await git.add(repopath, "*")
    await git.commit(repopath, message)


async def main() -> int:
    """Run the crawler."""
    logging.basicConfig(format=logging.BASIC_FORMAT, level=logging.INFO)

    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        "--interval",
        default=3600,
        type=int,
        help="update interval (seconds)",
    )
    parser.add_argument(
        "--window",
        default=3600 * 24,
        type=int,
        help="time window which is reloaded (seconds)",
    )
    parser.add_argument(
        "--git-repo",
        metavar="REPO",
        help="git repository where the output files are saved",
    )
    parser.add_argument(
        "--git-subdir",
        metavar="SUBDIR",
        help="subdirectory in the git repository where the output files are saved",
    )
    parser.add_argument(
        "--git-message",
        metavar="MSG",
        default="Update ranking files",
        help="commit message for the git repository",
    )
    parser.add_argument(
        "--git-no-push",
        action="store_true",
        help="don't push changes to the upstream repository",
    )
    args = parser.parse_args()

    if args.git_subdir is not None and os.path.isabs(args.git_subdir):
        logger.error("git-subdir option has to be a relative path")
        return 1

    # Create the API object and download the full thread- and posting list.
    window = dt.timedelta(seconds=args.window)
    gadse = TickerGadse(ticker_id=TICKER_ID, window=window)

    # Initialize the Git repository.
    dircontext: ContextManager[Optional[str]] = contextlib.nullcontext()
    if args.git_repo:
        dircontext = tempfile.TemporaryDirectory()

    with dircontext as repopath:
        if repopath:
            await git.clone(args.git_repo, repopath)

        while True:
            last_update = time.monotonic()
            await gadse.update()
            n = sum(gadse.ranking.values())
            logger.info(f"found {n} postings")

            if repopath:
                await commit_ranking(
                    gadse,
                    repopath=repopath,
                    subdir=args.git_subdir,
                    message=args.git_message,
                )
                if not args.git_no_push:
                    await git.push(repopath)

            wait_time = args.interval - (time.monotonic() - last_update)
            if wait_time < 0:
                logger.warning("update takes longer than interval")
            await asyncio.sleep(max(0, wait_time))

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
