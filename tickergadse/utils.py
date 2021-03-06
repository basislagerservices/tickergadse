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

"""Common utils for other modules."""

from typing import Callable, TypeVar


KT = TypeVar("KT")
VT = TypeVar("VT")


def join_dicts(
    a: dict[KT, VT], b: dict[KT, VT], *, op: Callable[[VT, VT], VT]
) -> dict[KT, VT]:
    """Join two dictionaries by adding their values."""
    result = dict(a)
    for k, v in b.items():
        try:
            result[k] = op(a[k], b[k])
        except KeyError:
            result[k] = v

    return result
