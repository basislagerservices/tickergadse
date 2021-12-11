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

"""Tests for git interface."""

import os

from tickergadse import git


async def test_git_init(tmp_path):
    """Create an empty git repository."""
    await git.init(tmp_path)
    assert os.path.exists(tmp_path / ".git")


async def test_git_repo_fixture_empty(git_repo):
    """Check if the fixture works for empty repositories."""
    repo = await git_repo()
    assert os.path.exists(repo / ".git")


async def test_git_repo_fixture_nonempty(git_repo):
    """Check if the fixture works for repos with files."""
    files = [
        ("foofile", "foocontent"),
        ("bar/barfile", "barcontent"),
        ("bar/ham/hamfile", "hamcontent"),
    ]
    repo = await git_repo(files)
    assert os.path.exists(repo / ".git")
    for file, content in files:
        assert os.path.exists(repo / file)
        mode = "rb" if isinstance(content, bytes) else "r"
        with open(repo / file, mode) as fp:
            assert fp.read() == content


async def test_git_clone_local(git_repo, tmp_path):
    """Clone from a local repository."""
    upstream = await git_repo()
    await git.clone(upstream, tmp_path / "local")
    assert os.path.exists(tmp_path / "local/.git")


async def test_git_clone_remote(tmp_path):
    """Clone from a remote repository."""
    REMOTE_REPO = "https://github.com/githubtraining/first-day-on-github.git"
    await git.clone(REMOTE_REPO, tmp_path)
    assert os.path.exists(tmp_path / ".git")


async def test_git_push(git_repo, tmp_path):
    """Push to a local repository."""
    upstream = await git_repo(bare=True)
    local = tmp_path / "local"
    await git.clone(upstream, local)
    with open(local / "foofile", "w") as fp:
        fp.write("foocontent")
    await git.add(local, "*")
    await git.commit(local, "Some update")
    await git.push(local)
