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

"""Crawler for the Seuchenticker Basislager."""

import argparse
import asyncio
import datetime as dt
import json
import logging
import os
import sys

from .gadse import TickerGadse, UpdateError


DESCRIPTION = (
    "Continuously update the postcount and other stats of a live ticker. "
    "Results are written to a file."
)

logger = logging.getLogger(__name__)


async def wait_until(target: dt.datetime, *, poll_interval: int = 1) -> None:
    """Wait until the given target time (in UTC without timezone info)."""
    logger.info(f"waiting until {target.isoformat()}")
    while dt.datetime.utcnow() < target:
        await asyncio.sleep(poll_interval)


async def main() -> int:
    """Run the crawler."""
    logging.basicConfig(format=logging.BASIC_FORMAT, level=logging.INFO)

    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        "--ticker-id",
        metavar="ID",
        action="append",
        type=int,
        required=True,
        help="ID of the ticker (allowed multiple times)",
    )
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
    parser.add_argument(
        "--once",
        action="store_true",
        help="run the crawler only once",
    )
    parser.add_argument(
        "--continue",
        action="store_true",
        dest="continue_flag",
        help="continue from a given persistent state if it exists",
    )
    parser.add_argument(
        "--state-file",
        help="path to the state file",
    )
    parser.add_argument(
        "--output",
        help="path to the output JSON file",
    )
    args = parser.parse_args()

    if args.continue_flag and not args.state_file:
        logger.error("can't continue without given state file")
        return 1

    # Create the API object and download the full thread- and posting list.
    window = dt.timedelta(seconds=args.window)
    gadse = TickerGadse(ticker_ids=args.ticker_id, window=window)
    if args.continue_flag:
        try:
            with open(args.state_file, "rb") as fpb:
                gadse.restore_state(fpb)
            logger.info("continuing from saved state")
        except FileNotFoundError:
            logger.info("state file does not exist. starting from blank state")
        except Exception:
            logger.exception("restoring state failed")

    next_update = dt.datetime.utcnow()
    while True:
        await wait_until(next_update)
        try:
            await gadse.update()
        except UpdateError:
            logger.exception("update failed")
            await asyncio.sleep(30)
            continue

        # Save the state.
        if args.state_file:
            if statedir := os.path.dirname(args.state_file):
                os.makedirs(statedir, exist_ok=True)
            with open(args.state_file, "wb") as fpb:
                gadse.save_state(fpb)

        n = sum(gadse.ranking.values())
        logger.info(f"found {n} postings")

        # Write ranking file.
        ranking = dict(
            date=gadse.last_update.strftime("%d.%m.%Y - %H:%M (UTC)"),
            users=[{"name": k.name, "postings": v} for k, v in gadse.ranking.items()],
        )
        if args.output:
            if outdir := os.path.dirname(args.output):
                os.makedirs(outdir, exist_ok=True)
            with open(args.output, "w") as fpt:
                json.dump(ranking, fpt, indent=4, sort_keys=True)

        if args.once:
            break

        while next_update < dt.datetime.utcnow():
            next_update += dt.timedelta(seconds=args.interval)

    return 0


def entrypoint() -> int:
    """Run the main crawler function in asyncio."""
    return asyncio.run(main())


if __name__ == "__main__":
    sys.exit(entrypoint())
