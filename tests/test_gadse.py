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

"""Tests for the tickergadse.gadse module."""


import asyncio
import datetime as dt

import pytest

from tickergadse.gadse import TickerGadse


@pytest.fixture
async def gadse():
    """Crawler for an old live ticker."""
    return TickerGadse(ticker_id=1336696633613, window=dt.timedelta(days=1))


async def test_deleted_users(gadse):
    """Check if deleted users are distinguished in the the ranking."""
    await gadse.update()
    deleted = {u.user_id for u in gadse.ranking.keys() if u.name == "gelöschter User"}
    assert len(deleted) > 1
