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

"""Common utils for other modules."""

import contextlib
import sys
import warnings


@contextlib.asynccontextmanager
async def asyncnullcontext(enter_result=None):  # type: ignore
    """Create a nullcontext for 'async with' statements."""
    version = (sys.version_info.major, sys.version_info.minor)
    if version >= (3, 10):
        warnings.warn(
            "'asyncnullcontext' should be replaced with 'contextlib.nullcontext'",
            DeprecationWarning,
        )
    yield enter_result
