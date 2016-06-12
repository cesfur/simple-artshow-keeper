# Artshow Keeper: A support tool for keeping an Artshow running.
# Copyright (C) 2014  Ivo Hanak
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import functools
import flask
import os

class UserGroups:
    ADMIN = 'admin'
    SCAN_DEVICE = 'scandevice'
    OTHERS = 'others'
    UNKNOWN = 'unknown'

def auth(allow=UserGroups.ADMIN):
    def decorator_auth_allow(func):
        @functools.wraps(func)
        def decorated_function(*args, **kwargs):            
            if flask.g.userGroup == UserGroups.ADMIN \
                    or (not isinstance(allow, list) and flask.g.userGroup == str(allow)) \
                    or (isinstance(allow, list) and flask.g.userGroup in allow):
                return func(*args, **kwargs)
            elif flask.g.userGroup == UserGroups.UNKNOWN:
                return flask.redirect(flask.url_for('authenticate', next=flask.request.full_path))
            else:
                return flask.abort(404)
        return decorated_function
    return decorator_auth_allow

def getNonZeroRandom(size=8):
    code = 0
    iteration = 0
    while code == 0 and iteration < 3:
        bytes = os.urandom(size)
        for byte in bytes:
            code = (code * 256) + byte
        iteration = iteration + 1
    return code
