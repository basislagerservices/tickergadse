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

"""Tests for the tickergadse.models module."""

import datetime as dt

import pytest

from tortoise import Tortoise

from tickergadse.models import User, Thread, Ticker


@pytest.fixture(scope="function", autouse=True)
async def tortoise_init(request):
    """Initialize the database.

    We only need this in this file. Otherwise the database is initialized by the
    application. This is mostly a reimplementation of the initializer in Tortoise,
    but it supports function scope.
    """
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": ["tickergadse.models"]},
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


async def test_database_create():
    """Insert a few models into the database."""
    await User.create(id=1000, name="Washington", registered=dt.date.today())
    await User.create(id=2000, name="Hamilton", registered=dt.date.today())

    users = await User.filter()
    assert len(users) == 2


async def test_ticker_thread_save():
    """Create objects with references to other objects and save them later."""
    ticker = Ticker(id=1000)
    await ticker.save()
    threads = [
        Thread(id=i, published=dt.datetime.now(), ticker=ticker) for i in range(16)
    ]
    for t in threads:
        await t.save()

    assert len(await Ticker.filter()) == 1
    assert len(await Thread.filter()) == 16
