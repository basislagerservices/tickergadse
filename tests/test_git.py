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
import shutil
from typing import Union

import pytest

from tickergadse import git


@pytest.fixture
def git_repo(tmp_path):
    """Create a git repository with optional files."""
    repopath = tmp_path / "upstream"

    def fixture(
        files: list[tuple[str, Union[bytes, str]]] = None,
        *,
        bare: bool = False,
    ) -> str:
        assert not files or not bare, "can't create bare repo with files"
        git.init(repopath, bare=bare)
        for path, content in files or []:
            assert not os.path.isabs(path)
            if d := os.path.dirname(os.path.join(repopath, path)):
                os.makedirs(os.path.join(repopath, d), exist_ok=True)

            mode = "wb" if isinstance(content, bytes) else "w"
            with open(os.path.join(repopath, path), mode) as fp:
                fp.write(content)

        if files:
            git.add(repopath, "*")
            git.commit(repopath, "Initial commit")

        return repopath

    return fixture


def test_git_init(tmp_path):
    """Create an empty git repository."""
    git.init(tmp_path)
    assert os.path.exists(tmp_path / ".git")


def test_git_repo_fixture_empty(git_repo):
    """Check if the fixture works for empty repositories."""
    repo = git_repo()
    assert os.path.exists(repo / ".git")


def test_git_repo_fixture_nonempty(git_repo):
    """Check if the fixture works for repos with files."""
    files = [
        ("foofile", "foocontent"),
        ("bar/barfile", "barcontent"),
        ("bar/ham/hamfile", "hamcontent"),
    ]
    repo = git_repo(files)
    assert os.path.exists(repo / ".git")
    for file, content in files:
        assert os.path.exists(repo / file)
        mode = "rb" if isinstance(content, bytes) else "r"
        with open(repo / file, mode) as fp:
            assert fp.read() == content


def test_git_clone_local(git_repo, tmp_path):
    """Clone from a local repository."""
    upstream = git_repo()
    git.clone(upstream, tmp_path / "local")
    assert os.path.exists(tmp_path / "local/.git")


def test_git_clone_remote(tmp_path):
    """Clone from a remote repository."""
    git.clone("https://github.com/githubtraining/first-day-on-github.git", tmp_path)
    assert os.path.exists(tmp_path / ".git")


def test_git_push(git_repo, tmp_path):
    """Push to a local repository."""
    upstream = git_repo(bare=True)
    local = tmp_path / "local"
    git.clone(upstream, local)
    with open(local / "foofile", "w") as fp:
        fp.write("foocontent")
    git.add(local, "*")
    git.commit(local, "Some update")
    git.push(local)