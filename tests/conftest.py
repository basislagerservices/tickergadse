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

"""Configuration for unit tests."""

import os
from typing import Union

import pytest

from tickergadse import git


@pytest.fixture
async def git_repo(tmp_path):
    """Create a git repository with optional files."""
    repopath = tmp_path / "upstream"

    async def fixture(
        files: list[tuple[str, Union[bytes, str]]] = None,
        *,
        bare: bool = False,
    ) -> str:
        assert not files or not bare, "can't create bare repo with files"
        await git.init(repopath, bare=bare)
        for path, content in files or []:
            assert not os.path.isabs(path)
            if d := os.path.dirname(os.path.join(repopath, path)):
                os.makedirs(os.path.join(repopath, d), exist_ok=True)

            mode = "wb" if isinstance(content, bytes) else "w"
            with open(os.path.join(repopath, path), mode) as fp:
                fp.write(content)

        if files:
            await git.add(repopath, "*")
            await git.commit(repopath, "Initial commit")

        return repopath

    return fixture
