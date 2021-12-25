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

"""Partially reverse-engineered API to derstandard.at."""


__all__ = ("DerStandardAPI",)


import asyncio
import concurrent.futures
import contextlib
import itertools
import time
from typing import Any, Optional, Union

from aiohttp import ClientSession

import dateutil.parser as dateparser

import pytz

from selenium import webdriver  # type: ignore
from selenium.webdriver.chrome.options import Options  # type: ignore
from selenium.webdriver.common.by import By  # type: ignore

from .dataclasses import Posting, Thread, User
from .utils import asyncnullcontext


@contextlib.contextmanager
def chromedriver() -> webdriver.Chrome:
    """Create a webdriver for Chrome."""
    try:
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")

        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(10)

        yield driver
    finally:
        driver.quit()


class DerStandardAPI:
    """API methods for derstandard.at."""

    def __init__(self) -> None:
        self._cookies: Optional[dict[str, str]] = None

    def URL(self, tail: str) -> str:
        """Construct an URL for a request."""
        return "https://www.derstandard.at/" + tail

    def session(self) -> ClientSession:
        """Create a client session with credentials."""
        return ClientSession(cookies=self._cookies)

    async def get_ticker_threads(
        self,
        ticker_id: Union[int, str],
        *,
        client_session: Optional[ClientSession] = None,
    ) -> list[Thread]:
        """Get a list of thread IDs of a ticker."""
        url = self.URL(f"/jetzt/api/redcontent?id={ticker_id}&ps=1000000")
        context = asyncnullcontext(client_session) if client_session else self.session()
        async with context as session:
            async with session.get(url) as resp:
                return [
                    Thread(
                        thread_id=t["id"],
                        published=dateparser.parse(t["ctd"]).astimezone(pytz.utc),
                        ticker_id=int(ticker_id),
                        title=t.get("hl") or None,
                        message=t.get("cm") or None,
                    )
                    for t in (await resp.json())["rcs"]
                ]

    async def _get_thread_postings_page(
        self,
        ticker_id: Union[int, str],
        thread_id: Union[int, str],
        skip_to: Union[None, int, str] = None,
        *,
        client_session: Optional[ClientSession] = None,
    ) -> Any:
        """Get a single page of postings from a ticker thread."""
        url = self.URL(
            f"/jetzt/api/postings?objectId={ticker_id}&redContentId={thread_id}"
        )
        if skip_to:
            url += f"&skipToPostingId={skip_to}"
        context = asyncnullcontext(client_session) if client_session else self.session()
        async with context as session:
            async with session.get(url) as resp:
                return await resp.json()

    async def get_thread_postings(
        self,
        ticker_id: Union[int, str],
        thread_id: Union[int, str],
        *,
        client_session: Optional[ClientSession] = None,
    ) -> list[Posting]:
        """Get all postings in a ticker thread."""
        postings = []
        page = await self._get_thread_postings_page(
            ticker_id,
            thread_id,
            client_session=client_session,
        )
        while page["p"]:
            postings.extend(page["p"])
            skip_to = page["p"][-1]["pid"]
            page = await self._get_thread_postings_page(
                ticker_id,
                thread_id,
                skip_to,
                client_session=client_session,
            )

        # Remove duplicates.
        postings = list({p["pid"]: p for p in postings}.values())
        return [
            Posting(
                posting_id=p["pid"],
                parent_id=p["ppid"],
                user=User(user_id=p["cid"], name=p["cn"]),
                thread_id=int(thread_id),
                published=dateparser.parse(p["cd"]).astimezone(pytz.utc),
                title=p.get("hl") or None,
                message=p.get("tx") or None,
            )
            for p in postings
        ]

    async def update_cookies(self) -> None:
        """Update credentials and GDPR cookies."""
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            self._cookies = await loop.run_in_executor(pool, self._accept_conditions)

    def _accept_conditions(self, timeout: Optional[int] = None) -> dict[str, str]:
        """Accept terms and conditions and return necessary cookies.

        Cookies are in a format suitable for the aiohttp.ClientSession.
        """
        with chromedriver() as driver:
            driver.get("https://www.derstandard.at/consent/tcf/")
            it = itertools.count() if timeout is None else range(int(timeout + 0.5))
            for _ in it:
                # Find the correct iframe
                for element in driver.find_elements(By.TAG_NAME, "iframe"):
                    if element.get_attribute("title") == "SP Consent Message":
                        driver.switch_to.frame(element)
                        # Find the correct button and click it.
                        for button in driver.find_elements(By.TAG_NAME, "button"):
                            if button.get_attribute("title") == "Einverstanden":
                                button.click()
                                return {
                                    c["name"]: c["value"] for c in driver.get_cookies()
                                }
                    time.sleep(1)
            else:
                raise TimeoutError("accepting terms and conditions timed out")
