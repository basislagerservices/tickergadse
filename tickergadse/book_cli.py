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

"""Book generator for the Seuchenticker Basislager."""

import argparse
import asyncio
import logging
import sys


TICKER_ID = 2000130527798

logger = logging.getLogger(__name__)


async def main() -> int:
    """Run the book generator."""
    logging.basicConfig(format=logging.BASIC_FORMAT, level=logging.INFO)

    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    return 0


def entrypoint() -> int:
    """Run the main book generator function in asyncio."""
    return asyncio.run(main())


if __name__ == "__main__":
    sys.exit(entrypoint())
