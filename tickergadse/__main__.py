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

"""Crawler for the Seuchenticker Basislager."""

import argparse
import asyncio
import datetime as dt
import json
import logging
import operator
import os
import sys
from typing import Any, Optional

from aiohttp import ClientSession

import pytz

from .api import DerStandardAPI
from .dataclasses import Posting, Thread
from .utils import join_dicts


TICKER_ID = 2000130527798


logger = logging.getLogger("tickergadse")


class TickerGadse:
    """Crawler for the ticker."""

    def __init__(
        self, window: dt.timedelta, *, retries: int = 5, delay: int = 2
    ) -> None:
        self._window = window
        self._retries = retries
        self._delay = delay
        self._api = DerStandardAPI()

        # Only save the number of postings for threads outside the window.
        self._retired_postcount: dict[str, int] = dict()

        # Threads that are part of the history.
        self._retired_threads: set[Thread] = set()

    async def update(self) -> dict[str, int]:
        """Update the state of the crawler."""
        for _ in range(self._retries):
            try:
                # Update cookies here, because we can't really detect if we got them
                # without seeing if a aiohttp request fails.
                await self._api.update_cookies()
                threads = await self._api.get_ticker_threads(TICKER_ID)
                break
            except Exception as e:
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
        active: dict[str, int] = dict()
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
                logger.info(f"retiring thread {t.thread_id}")
            else:
                active = join_dicts(
                    self._retired_postcount,
                    stats,
                    op=operator.add,
                )
                logger.info(f"active thread {t.thread_id}")

        return join_dicts(self._retired_postcount, active, op=operator.add)

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
                    TICKER_ID,
                    tid,
                    client_session=client_session,
                )
                break
            except Exception as e:
                logger.exception(f"failed to get postings for thread {tid}")
                await asyncio.sleep(self._delay)

        raise ConnectionError("failed to download postings")

    def _posting_stats(self, postings: list[Posting]) -> dict[str, int]:
        """Get posting stats for a single thread."""
        result: dict[str, int] = dict()
        for p in postings:
            result[p.user] = result.get(p.user, 0) + 1
        return result


async def main() -> int:
    """Run the crawler."""
    logging.basicConfig(format=logging.BASIC_FORMAT, level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--interval",
        default=3600,
        type=int,
        help="update interval (seconds)",
    )
    parser.add_argument(
        "--window",
        default=3600 * 24,
        type=int,
        help="time window which is reloaded (seconds)",
    )
    args = parser.parse_args()

    # Create the API object and download the full thread- and posting list.
    window = dt.timedelta(seconds=args.window)
    gadse = TickerGadse(window=window)

    while True:
        await gadse.update()
        await asyncio.sleep(args.interval)

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
