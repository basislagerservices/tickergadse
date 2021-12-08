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

"""Models for the database."""


__all__ = ("Posting", "User", "Ticker", "Thread")


# TODO: Figure out how to handle mutable fields.

from tortoise import fields
from tortoise.models import Model


class User(Model):
    """Class for a user."""

    id = fields.IntField(pk=True)
    name = fields.TextField()
    registered = fields.DateField()
    crawled = fields.DatetimeField(null=True)


class Posting(Model):
    """Class for a published posting."""

    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="postings")
    thread = fields.ForeignKeyField("models.Thread", related_name="postings")
    parent = fields.ForeignKeyField("models.Posting", related_name="children")
    message = fields.TextField()
    published = fields.DatetimeField()
    crawled = fields.DatetimeField(null=True)


class Ticker(Model):
    """Class for a live ticker."""

    id = fields.IntField(pk=True)
    crawled = fields.DatetimeField(null=True)


class Thread(Model):
    """Class for a live ticker thread."""

    id = fields.IntField(pk=True)
    published = fields.DatetimeField()
    ticker = fields.ForeignKeyField("models.Ticker", related_name="threads")
    crawled = fields.DatetimeField(null=True)
