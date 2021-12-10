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

"""Tests for utils module."""

import operator

from tickergadse.utils import asyncnullcontext, join_dicts


async def test_asyncnullcontext():
    """Check if asyncnullcontext works."""
    async with asyncnullcontext("foo") as foo:
        assert foo == "foo"


async def test_asyncnullcontext_noparam():
    """Check if asyncnullcontext works."""
    async with asyncnullcontext() as foo:
        assert foo is None


async def test_join_dicts():
    """Check if two dictionaries are joined."""
    a = {"a": 1, "b": 2}
    b = {"b": 3, "c": 4}

    assert join_dicts(a, b, op=operator.add) == {"a": 1, "b": 5, "c": 4}
