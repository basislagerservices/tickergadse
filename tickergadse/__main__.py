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
import datetime as dt
import logging
import sys

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
        default=".",
        help="subdirectory in the git repository where the output files are saved",
    )
    parser.add_argument(
        "--git-message",
        metavar="MSG",
        default="Update ranking files",
        help="commit message for the git repository",
    )
    args = parser.parse_args()

    # Create the API object and download the full thread- and posting list.
    window = dt.timedelta(seconds=args.window)
    gadse = TickerGadse(ticker_id=TICKER_ID, window=window)

    while True:
        await gadse.update()
        n = sum(gadse.ranking.values())
        logger.info(f"found {n} postings")
        await asyncio.sleep(args.interval)

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
