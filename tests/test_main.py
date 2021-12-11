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

"""Tests for the tickergadse.__main__ module."""


import datetime as dt
import os
from unittest.mock import MagicMock

from tickergadse.__main__ import commit_ranking


async def test_commit_ranking(git_repo):
    """Check if we can commit a ranking to a repository."""
    repopath = await git_repo()

    gadse = MagicMock()
    gadse.last_update = dt.datetime.utcnow()
    gadse.ranking = {"a": 1000, "b": 2000}

    await commit_ranking(
        gadse,
        repopath=repopath,
        subdir="foo/bar",
        message="some message",
    )
    resultpath = os.path.join(repopath, "foo/bar/ranking.json")
    assert os.path.exists(resultpath)
