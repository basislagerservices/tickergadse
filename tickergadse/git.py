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

"""Basic interface to Git."""

import subprocess as sp


def init(repo: str, *, bare: bool = False) -> None:
    """Initialize an empty repository."""
    options: list[str] = []
    if bare:
        options.append("--bare")
    sp.run(["git", "init"] + options + [repo], check=True)


def clone(upstream: str, local: str) -> None:
    """Clone a repository to a local directory."""
    sp.run(["git", "clone", upstream, local], check=True)


def add(repo: str, *files: str) -> None:
    """Add files to the index."""
    sp.run(["git", "add"] + list(files), cwd=repo, check=True)


def commit(repo: str, message: str) -> None:
    """Commit changes to the repository."""
    sp.run(["git", "commit", "-m", message], cwd=repo, check=True)


def push(repo: str) -> None:
    """Push the changes."""
    sp.run(["git", "push"], cwd=repo, check=True)


def pull(repo: str) -> None:
    """Pull changes."""
    sp.run(["git", "pull"], cwd=repo, check=True)
