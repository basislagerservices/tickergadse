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

import asyncio
import logging
import shlex
from pathlib import PosixPath
from typing import Optional, Sequence, Union


logger = logging.getLogger(__name__)


async def _run(
    command: Sequence[Union[str, PosixPath]],
    *,
    cwd: Optional[str] = None,
) -> tuple[str, str]:
    """Run a shell command."""
    cmdstr = " ".join(shlex.quote(str(c)) for c in command)
    logger.debug("calling: {cmdstr}")
    proc = await asyncio.create_subprocess_shell(
        cmdstr,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return stdout.decode(), stderr.decode()


async def init(repo: str, *, bare: bool = False) -> None:
    """Initialize an empty repository."""
    command = ["git", "init"]
    if bare:
        command.append("--bare")
    command.append(repo)
    await _run(command)


async def clone(upstream: str, local: str) -> None:
    """Clone a repository to a local directory."""
    await _run(["git", "clone", upstream, local])


async def add(repo: str, *files: str) -> None:
    """Add files to the index."""
    await _run(["git", "add"] + list(files), cwd=repo)


async def commit(repo: str, message: str) -> None:
    """Commit changes to the repository."""
    await _run(["git", "commit", "-m", message], cwd=repo)


async def push(repo: str) -> None:
    """Push the changes."""
    await _run(["git", "push"], cwd=repo)


async def pull(repo: str) -> None:
    """Pull changes."""
    await _run(["git", "pull"], cwd=repo)
