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
import logging
import os
import sys
from typing import Optional, Type

from .api import DerStandardAPI
from .book import Book
from .dataclasses import Thread


DESCRIPTION = (
    "Generate a book from logbook entries."
    "Output paths are absolute if no Git repository is given, "
    "or relative to the Git repository if one is given."
)

TICKER_ID = 2000130527798

logger = logging.getLogger(__name__)


class Logbook(Book):
    """Unsin(n)kable III Logbook."""

    title = "Unsin(n)kable III"
    subtitle = "Geschichten aus dem Leben von wahnsinnigen Seeleuten"
    author = "angmar hexenkönig"

    def is_book_thread(self, thread: Thread) -> bool:
        """Determine if a thread is a logbook entry."""
        if not thread.title or not thread.message:
            return False

        if "Unsin(n)kable" in thread.title and (
            "Logbuch" in thread.title or "Notizbuch" in thread.title
        ):
            return True

        if "Vorläufiger Abschlussbericht der Hafenkommandantur Havanna" in thread.title:
            return True

        return False


class Ersterpreis(Book):
    """Raumschiff Ersterpreis book."""

    title = "Raumschiff Ersterpreis"
    subtitle = "Geschichten aus dem Leben von wahnsinnigen AstronautInnen"
    author = "Lord Suggs"

    def is_book_thread(self, thread: Thread) -> bool:
        """Determine if a thread is a logbook entry."""
        return bool(thread.title and thread.message and "Ersterpreis" in thread.title)

    def format_message(self, thread: Thread) -> Optional[str]:
        """Convert # in some threads to bullet points."""
        if thread.thread_id == 1000249559:
            assert thread.message is not None
            return "".join(
                self.reformat_line(line)
                for line in thread.message.splitlines(keepends=True)
            )
        return thread.message

    def reformat_line(self, line: str) -> str:
        """Convert # at the beginning of the line to *."""
        if line.startswith("# "):
            return "* " + line[2:]
        return line


BOOKS: dict[str, Type[Book]] = {
    "logbook": Logbook,
    "ersterpreis": Ersterpreis,
}


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
        "--book",
        "-b",
        required=True,
        choices=BOOKS.keys(),
        help="type of book to generate",
    )
    args = parser.parse_args()

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
    book = BOOKS[args.book](threads)
    logger.info(f"found {len(book.threads)} logbook entries")

    # Generate the books.
    for output in [os.path.abspath(p) for p in args.output]:
        book.create_book(output)

    return 0


def entrypoint() -> int:
    """Run the main book generator function in asyncio."""
    return asyncio.run(main())


if __name__ == "__main__":
    sys.exit(entrypoint())
