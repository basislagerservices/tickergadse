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

"""Tests for the tickergadse.gadse module."""


import datetime as dt
import io
import pickle

import pytest

from tickergadse.gadse import TickerGadse


@pytest.fixture
async def gadse():
    """Crawler for an old live ticker."""
    return TickerGadse(ticker_ids=[1336696633613], window=dt.timedelta(days=1))


async def test_deleted_users(gadse):
    """Check if deleted users are distinguished in the ranking."""
    await gadse.update()
    deleted = {u.user_id for u in gadse.ranking.keys() if u.name == "gelöschter User"}
    assert len(deleted) > 1


@pytest.mark.parametrize(
    "gadse_ids,state_ids",
    [
        pytest.param((1, 2, 3), (1, 2, 3), id="same-IDs"),
        pytest.param((1, 2), (1, 2, 3), id="state-superset"),
        pytest.param((1, 2, 3), (1, 2), id="state-subset"),
    ],
)
async def test_restore_state(gadse_ids, state_ids):
    """Restore the state."""
    # First generate the state to restore from.
    def state(i):
        return TickerGadse.PersistentState(i, last_update=dt.datetime.utcnow())

    state = tuple(state(i) for i in state_ids)
    statefp = io.BytesIO(pickle.dumps(state))

    # Create the original crawler and then restore the state.
    gadse = TickerGadse(gadse_ids, dt.timedelta(hours=24))
    gadse.restore_state(statefp)

    assert (
        tuple(s.ticker_id for s in gadse._states) == gadse_ids
    ), "ticker_id added to or removed from state"

    common_ids = set.intersection(set(gadse_ids), set(state_ids))
    updated_states = [s for s in gadse._states if s.ticker_id in common_ids]
    remaining_states = [s for s in gadse._states if s.ticker_id not in common_ids]
    assert all(s in state for s in updated_states), "state not updated"
    assert all(s not in state for s in remaining_states), "wrong state updated"
