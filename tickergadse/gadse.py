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

"""Crawler logic for a single ticker."""

from __future__ import annotations
import asyncio
import datetime as dt
import logging
import operator
import pickle
import time
from dataclasses import dataclass, field
from typing import BinaryIO, Iterable, Optional

from aiohttp import ClientSession

import pytz

from .api import DerStandardAPI
from .dataclasses import Posting, Thread, User
from .utils import join_dicts

logger = logging.getLogger(__name__)


class UpdateError(Exception):
    """Error during update."""


class TickerGadse:
    """Crawler for one or multiple ticker."""

    @dataclass
    class PersistentState:
        """Persistent state of the crawler."""

        ticker_id: int
        """ID of the ticker to crawl."""

        retired_postcount: dict[User, int] = field(default_factory=dict)
        """Number of postings in retired threads."""

        active_postcount: dict[User, int] = field(default_factory=dict)
        """Number of postings in active threads."""

        retired_threads: set[Thread] = field(default_factory=set)
        """Retired threads."""

        last_update: dt.datetime = dt.datetime(1970, 1, 1)
        """Time of the last update."""

    def __init__(
        self,
        ticker_ids: Iterable[int],
        window: dt.timedelta,
        *,
        retries: int = 5,
        delay: int = 10,
    ) -> None:
        self._window = window
        self._retries = retries
        self._delay = delay
        self._api = DerStandardAPI()

        self._states = tuple(TickerGadse.PersistentState(i) for i in ticker_ids)

    def save_state(self, fp: BinaryIO) -> None:
        """Save the state to a buffer."""
        pickle.dump(self._states, fp)

    def restore_state(self, fp: BinaryIO) -> None:
        """Restore the state from a buffer."""
        states = pickle.load(fp)
        if not all(isinstance(s, TickerGadse.PersistentState) for s in states):
            raise TypeError("invalid type restored from persistent state")

        if {s.ticker_id for s in states} != {s.ticker_id for s in self._states}:
            raise ValueError("ticker IDs of state don't match")

        self._states = states

    async def update(self) -> None:
        """Update the state of the crawler."""
        for s in self._states:
            await self._update(s)

    async def _update(self, state: TickerGadse.PersistentState) -> None:
        """Update the state of a single crawler."""
        start_time = time.monotonic()
        for _ in range(self._retries):
            try:
                # Update cookies here, because we can't really detect if we got them
                # without seeing if a aiohttp request fails.
                await self._api.update_cookies()
                threads = await self._api.get_ticker_threads(state.ticker_id)
                break
            except Exception:
                logger.exception("failed to get ticker threads")
                await asyncio.sleep(self._delay)
        else:
            logger.error("update failed")
            raise UpdateError("cookie or thread update failed")

        logger.info(f"found {len(threads)} threads")

        # Download postings for new or active threads.
        update_threads = list(set(threads) - state.retired_threads)
        update_threads.sort(key=lambda t: t.published)
        session = self._api.session()
        requests = [
            self._get_postings(t, client_session=session) for t in update_threads
        ]
        async with session:
            postings = await asyncio.gather(*requests)

        now = dt.datetime.now().astimezone(pytz.utc)
        active_threads: dict[User, int] = dict()

        # For logging
        active_count = 0
        retired_count = 0
        for t, p in zip(update_threads, postings):
            # If the thread is outside the window, then we retire it and update the
            # number of retired postings.
            stats = self._posting_stats(p)
            if t.published < now - self._window:
                state.retired_threads.add(t)
                state.retired_postcount = join_dicts(
                    state.retired_postcount,
                    stats,
                    op=operator.add,
                )
                retired_count += 1
            else:
                active_threads = join_dicts(
                    active_threads,
                    stats,
                    op=operator.add,
                )
                active_count += 1

        logger.info(
            f"finished update with {retired_count} newly retired and {active_count} "
            "active threads"
        )
        duration = time.monotonic() - start_time
        logger.info(f"update took {duration:.02f} seconds")
        state.active_postcount = active_threads
        state.last_update = dt.datetime.utcnow()

    @property
    def ranking(self) -> dict[User, int]:
        """Get the current ranking."""
        ranking: dict[User, int] = dict()
        for state in self._states:
            ranking = join_dicts(ranking, state.retired_postcount, op=operator.add)
            ranking = join_dicts(ranking, state.active_postcount, op=operator.add)
        return ranking

    @property
    def last_update(self) -> dt.datetime:
        """Get the time of the last update.

        This is only for statistics, so we simply return the latest update.
        """
        return max(s.last_update for s in self._states)

    async def _get_postings(
        self,
        thread: Thread,
        *,
        client_session: Optional[ClientSession] = None,
    ) -> list[Posting]:
        """Get postings for a given thread."""
        for _ in range(self._retries):
            try:
                return await self._api.get_thread_postings(
                    thread.ticker_id,
                    thread.thread_id,
                    client_session=client_session,
                )
            except Exception:
                logger.exception(
                    f"failed to get postings for thread {thread.thread_id}"
                    f" in ticker {thread.ticker_id}"
                )
                await asyncio.sleep(self._delay)

        raise UpdateError("failed to download postings")

    def _posting_stats(self, postings: list[Posting]) -> dict[User, int]:
        """Get posting stats for a single thread."""
        result: dict[User, int] = dict()
        for p in postings:
            result[p.user] = result.get(p.user, 0) + 1
        return result
