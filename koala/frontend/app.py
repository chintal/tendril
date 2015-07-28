"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


# This is the WSGI compliant web application object
app = Flask(__name__)


# This is an SQLAlchemy ORM object.
#
# For the moment it points to a separate DB holding only app specific information, i.e., access control
# mechanisms only. The fundamental difference between this db instance and the one provided by utils.db
# is that this relies on Flask-SQLAlchemy provided db.Model and it's session management. The app should
# filter and do whatever it needs to based on the app DB and then pass whatever information is necessary
# to the underlying core via traditional function calls.
#
# This should be revisited at some point to reintegrate the DBs, either by switching to the correct Base
# within the Flask-SQLAlchemy (and sorting out the consequences to session management, as well as ensuring
# that the Base is compatible with what Flask plugins expect), or rewriting the Flask plugins to work with
# the vanilla Base.
db = SQLAlchemy(app)
