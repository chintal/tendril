#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2015 Chintalagiri Shashank
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
Docstring for helpers
"""

from tendril.frontend.app import app


@app.context_processor
def inject_version():
    import tendril
    return {'tendril_version': tendril.__version__}


@app.context_processor
def inject_instance_owner():
    from tendril.utils.config import COMPANY_NAME
    from tendril.utils.config import INSTANCE_SOURCES
    from tendril.utils.config import INSTANCE_FOLDER_SOURCES
    from tendril.utils.config import INSTANCE_DOCUMENTATION_PATH
    from datetime import date
    return {'instance_owner': COMPANY_NAME,
            'copyright_year': date.today().year,
            'instance_sources': INSTANCE_SOURCES,
            'instance_folder_sources': INSTANCE_FOLDER_SOURCES,
            'instance_documentation_path': INSTANCE_DOCUMENTATION_PATH,
            }


def lineplot_filter(s):
    return s


def histogram_filter(s):
    return s
