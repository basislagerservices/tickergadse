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

"""Book generator for the Seuchenticker Basislager."""

import argparse
import asyncio
import contextlib
import logging
import os
import subprocess
import sys
import tempfile
from typing import ContextManager, Optional

from . import git
from .api import DerStandardAPI
from .dataclasses import Thread


DESCRIPTION = (
    "Generate a book from logbook entries."
    "Output paths are absolute if no Git repository is given, "
    "or relative to the Git repository if one is given."
)

TICKER_ID = 2000130527798

logger = logging.getLogger(__name__)


async def main() -> int:
    """Run the book generator."""
    logging.basicConfig(format=logging.BASIC_FORMAT, level=logging.INFO)

    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        "--output",
        "-o",
        action="append",
        help="output file",
    )
    parser.add_argument(
        "--git-repo",
        metavar="REPO",
        help="git repository where the output files are saved",
    )
    parser.add_argument(
        "--git-message",
        metavar="MSG",
        default="Update books",
        help="commit message for the git repository",
    )
    parser.add_argument(
        "--git-no-push",
        action="store_true",
        help="don't push changes to the upstream repository",
    )
    args = parser.parse_args()

    if args.git_repo is not None and any(os.path.isabs(p) for p in args.output):
        logger.error("output paths have to be relative when git repo is specified")
        return 1

    # Get threads in the ticker.
    api = DerStandardAPI()
    for _ in range(5):
        try:
            await api.update_cookies()
            threads = await api.get_ticker_threads(TICKER_ID)
            break
        except Exception:
            logger.exception("downloading ticker threads failed")
            await asyncio.sleep(5)
    else:
        logger.error("downloading ticker threads failed")
        return 1

    logger.info(f"found {len(threads)} threads")

    # Filter threads with logbook entries.
    # TODO: Move this into a configuration file.
    def is_logbook_thread(thread: Thread) -> bool:
        """Determine if a thread is a logbook entry."""
        return bool(
            thread.title
            and thread.message
            and "Unsin(n)kable" in thread.title
            and ("Logbuch" in thread.title or "Notizbuch" in thread.title)
        )

    bookthreads = [t for t in threads if is_logbook_thread(t)]
    bookthreads.sort(key=lambda t: t.published)
    logger.info(f"found {len(bookthreads)} logbook entries")

    dircontext: ContextManager[Optional[str]] = contextlib.nullcontext()
    if args.git_repo:
        dircontext = tempfile.TemporaryDirectory()

    # Create the book chapters and call pandoc to generate the output products.
    with tempfile.TemporaryDirectory() as tempdir, dircontext as repopath:
        for i, thread in enumerate(bookthreads):
            with open(os.path.join(tempdir, f"entry_{i}.md"), "w") as fp:
                fp.write("\n\\newpage")
                fp.write(f"# {thread.title}\n\n")
                assert thread.message is not None
                fp.write(thread.message)

        # TODO: Move this into a configuration file and get authors from downloaded
        #       threads.
        meta = {
            "title": "Unsin(n)kable III",
            "subtitle": "Geschichten aus dem Leben von wahnsinnigen Seeleuten",
            "papersize": "a5",
            "geometry": "margin=2cm",
            "author": "angmar hexenkönig",
        }
        metaopts = []
        for k, v in meta.items():
            metaopts.extend(["-M", f"{k}={v}"])

        # Set the output paths, clone the repo and create the necessary subdirectories
        # in the cloned repository.
        outputs = [os.path.abspath(output) for output in args.output]
        if repopath:
            await git.clone(args.git_repo, repopath)
            outputs = [os.path.join(repopath, output) for output in args.output]
            for output in outputs:
                os.makedirs(os.path.dirname(output), exist_ok=True)

        # Generate the book
        entries = [
            os.path.join(tempdir, f"entry_{i}.md") for i in range(len(bookthreads))
        ]
        for output in outputs:
            subprocess.run(["pandoc"] + metaopts + ["-o", output] + entries)

        # Commit changes and push them.
        if repopath:
            await git.add(repopath, "*")
            await git.commit(repopath, args.git_message)

            if not args.git_no_push:
                await git.push(repopath)

    return 0


def entrypoint() -> int:
    """Run the main book generator function in asyncio."""
    return asyncio.run(main())


if __name__ == "__main__":
    sys.exit(entrypoint())
