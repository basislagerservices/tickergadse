#
# Copyright 2021-2022 Basislager Services
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

"""Utilities for generating and managing generated books."""


import os
import shutil
import subprocess
import tempfile
from abc import ABC, abstractmethod
from typing import Iterable, Optional, Tuple

from .dataclasses import Thread


class Book(ABC):
    """Abstract book class for generating a book from raw thread postings."""

    titlepage: Optional[str] = None
    """Path to the title page."""

    title: Optional[str] = None
    """Title of the book."""

    subtitle: Optional[str] = None
    """Subtitle of the book."""

    papersize: str = "a5"
    """Size of the paper."""

    documentclass: str = "scrartcl"
    """Document class for pandoc."""

    # TODO: Remove this when authors are detected automatically.
    author: Optional[str] = None
    """Author of the book."""

    def __init__(self, threads: Iterable[Thread]) -> None:
        self._threads = [t for t in threads if self.is_book_thread(t)]
        self._threads.sort(key=lambda t: t.published)
        self._authors = list({t.user.name for t in self.threads})
        self._authors.sort()

    @abstractmethod
    def is_book_thread(self, t: Thread) -> bool:
        """Determine if a thread is part of the book."""
        raise NotImplementedError("method not implemented")

    @property
    def threads(self) -> Tuple[Thread, ...]:
        """Get the list of relevant threads."""
        return tuple(self._threads)

    def create_book(self, path: str) -> None:
        """Create the book at the given path."""
        fmt = os.path.splitext(path)[1]
        if fmt not in (".epub", ".pdf"):
            raise ValueError(f'invalid output format "{fmt[1:]}"')

        # TODO: Implement title pages
        metaopts = []
        if self.titlepage:
            raise NotImplementedError("title pages not supported")

        # TODO: Detect configuration values without hardcoding them.
        for option in ("title", "subtitle", "papersize", "documentclass", "author"):
            if value := getattr(self, option):
                metaopts.extend(["-M", f"{option}={value}"])

        # Write book chapters.
        with tempfile.TemporaryDirectory() as tempdir:
            entries = []
            for i, thread in enumerate(self.threads):
                entrypath = os.path.join(tempdir, f"entry_{i}.md")
                entries.append(entrypath)
                with open(entrypath, "w") as fp:
                    fp.write("\n\\newpage")
                    fp.write(f"# {thread.title}\n\n")
                    message = self.format_message(thread)
                    assert message is not None
                    fp.write(message)

            # Create in a temporary file so we don't create unnecessary directories
            # in case this fails.
            outfile = tempfile.mktemp(suffix=fmt)

            # TODO: Use asyncio for this. Not really necessary, but since this is
            #       called from a coroutine, it would make more sense.
            subprocess.run(["pandoc"] + metaopts + ["-o", outfile] + entries)

            # Create the tree and move the output file.
            os.makedirs(os.path.dirname(path), exist_ok=True)
            shutil.move(outfile, path)

    def format_message(self, thread: Thread) -> Optional[str]:
        """Reformat a message before writing.

        Some postings are poorly formatted, so we process them before writing. Takes
        the thread as an argument and returns the message in markdown.
        """
        return thread.message
