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

import asyncio
import datetime as dt
import logging
import operator
import time
from typing import Optional

from aiohttp import ClientSession

import pytz

from .api import DerStandardAPI
from .dataclasses import Posting, Thread
from .utils import join_dicts

logger = logging.getLogger(__name__)


class TickerGadse:
    """Crawler for the ticker."""

    def __init__(
        self, ticker_id: int, window: dt.timedelta, *, retries: int = 5, delay: int = 10
    ) -> None:
        self._ticker_id = ticker_id
        self._window = window
        self._retries = retries
        self._delay = delay
        self._api = DerStandardAPI()

        # Only save the number of postings for threads outside the window.
        self._retired_postcount: dict[str, int] = dict()
        self._active_postcount: dict[str, int] = dict()

        # Threads that are part of the history.
        self._retired_threads: set[Thread] = set()

        # Store the last update time.
        self._last_update = dt.datetime(1970, 1, 1)

    async def update(self) -> None:
        """Update the state of the crawler."""
        start_time = time.monotonic()
        for _ in range(self._retries):
            try:
                # Update cookies here, because we can't really detect if we got them
                # without seeing if a aiohttp request fails.
                await self._api.update_cookies()
                threads = await self._api.get_ticker_threads(self._ticker_id)
                break
            except Exception:
                logger.exception("failed to get ticker threads")
                await asyncio.sleep(self._delay)
        else:
            logger.error("update failed")
            return

        logger.info(f"found {len(threads)} threads")

        # Download postings for new or active threads.
        update_threads = list(set(threads) - self._retired_threads)
        update_threads.sort(key=lambda t: t.published)
        session = self._api.session()
        requests = [
            self._get_postings(t, client_session=session) for t in update_threads
        ]
        async with session:
            postings = await asyncio.gather(*requests)

        now = dt.datetime.now().astimezone(pytz.utc)
        active_threads: dict[str, int] = dict()

        # For logging
        active_count = 0
        retired_count = 0
        for t, p in zip(update_threads, postings):
            # If the thread is outside the window, then we retire it and update the
            # number of retired postings.
            stats = self._posting_stats(p)
            if t.published < now - self._window:
                self._retired_threads.add(t)
                self._retired_postcount = join_dicts(
                    self._retired_postcount,
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
        self._active_postcount = active_threads
        self._last_update = dt.datetime.utcnow()

    @property
    def ranking(self) -> dict[str, int]:
        """Get the current ranking."""
        return join_dicts(
            self._retired_postcount,
            self._active_postcount,
            op=operator.add,
        )

    @property
    def last_update(self) -> dt.datetime:
        """Get the time of the last update."""
        return self._last_update

    async def _get_postings(
        self,
        thread: Thread,
        *,
        client_session: Optional[ClientSession] = None,
    ) -> list[Posting]:
        """Get postings for a given thread."""
        tid = thread.thread_id
        for _ in range(self._retries):
            try:
                return await self._api.get_thread_postings(
                    self._ticker_id,
                    tid,
                    client_session=client_session,
                )
                break
            except Exception:
                logger.exception(f"failed to get postings for thread {tid}")
                await asyncio.sleep(self._delay)

        raise ConnectionError("failed to download postings")

    def _posting_stats(self, postings: list[Posting]) -> dict[str, int]:
        """Get posting stats for a single thread."""
        result: dict[str, int] = dict()
        for p in postings:
            result[p.user] = result.get(p.user, 0) + 1
        return result
