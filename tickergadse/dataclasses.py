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

import datetime as dt
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Thread:
    """Dataclass for threads."""

    thread_id: int
    """ID of this thread."""
    published: dt.datetime
    """Datetime this posting was published."""
    ticker_id: int
    """ID of the ticker this thread belongs to."""


@dataclass(frozen=True)
class Posting:
    """Dataclass for postings."""

    posting_id: int
    """ID of this posting."""
    parent_id: Optional[int]
    """Optional ID of a parent posting."""
    user: str
    """The user who posted this."""
    thread_id: int
    """ID of the thread this posting belongs to."""
    message: str
    """Content of the posting."""
    published: dt.datetime
    """Datetime this posting was published."""