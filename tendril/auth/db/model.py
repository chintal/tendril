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
Docstring for model.py
"""


from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy import Boolean
from sqlalchemy import DateTime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref

from flask_user import UserMixin

from tendril.utils.db import DeclBase
from tendril.utils.db import BaseMixin

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


# Define the UserRoles association model
class UserRoles(DeclBase, BaseMixin):
    user_id = Column(Integer(),
                     ForeignKey('User.id', ondelete='CASCADE'))
    role_id = Column(Integer(),
                     ForeignKey('Role.id', ondelete='CASCADE'))


# Define the User data model. Make sure to add the flask_user.UserMixin !!
class User(DeclBase, BaseMixin, UserMixin):

    # User email information (required for Flask-User)
    email = Column(String(255), nullable=False, unique=True)
    confirmed_at = Column(DateTime())

    # User information
    active = Column('is_active', Boolean(),
                    nullable=False, server_default='0')
    full_name = Column(String(50), nullable=False, server_default='')

    # Relationships
    user_auth = relationship('UserAuth', uselist=False)
    roles = relationship('Role', secondary=UserRoles.__table__,
                         backref=backref('users', lazy='dynamic'))


# Define the UserAuth data model.
class UserAuth(DeclBase, BaseMixin, UserMixin):
    user_id = Column(Integer(),
                     ForeignKey('User.id', ondelete='CASCADE'))

    # User authentication information (required for Flask-User)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False, server_default='')
    reset_password_token = Column(String(100),
                                  nullable=False, server_default='')
    active = Column(Boolean(), nullable=False, server_default='0')

    # Relationships
    user = relationship('User', uselist=False)


# Define the Role data model
class Role(DeclBase, BaseMixin):
    name = Column(String(50), unique=True)
    description = Column(String(255))

