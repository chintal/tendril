#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2016 Chintalagiri Shashank
#
# This file is part of tendril.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Docstring for controller
"""

from tendril.utils.db import with_db

from .model import User
from .model import UserAuth


@with_db
def get_users_list(session=None):
    return session.query(User.full_name).all()


@with_db
def get_username_from_full_name(full_name=None, session=None):
    return session.query(UserAuth.username).filter(
            UserAuth.user.has(full_name=full_name)
    ).one().username


@with_db
def get_user_object(username=None, session=None):
    return session.query(User).filter(User.user_auth.has(username=username)).one()

