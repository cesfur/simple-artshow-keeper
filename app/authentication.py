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

class UserGroups:
    ADMIN = 'admin'
    USERS = 'users'

def admin_auth_required(func):
    @functools.wraps(func)
    def decorated_function(*args, **kwargs):
        if flask.g.userGroup != UserGroups.ADMIN:
            return flask.redirect(flask.url_for('login', next=flask.request.url))
        else:
            return func(*args, **kwargs)
    return decorated_function

def user_auth_required(func):
    @functools.wraps(func)
    def decorated_function(*args, **kwargs):
        if flask.g.userGroup not in [UserGroups.ADMIN, UserGroups.USERS]:
            return flask.redirect(flask.url_for('login', next=flask.request.url))
        else:
            return func(*args, **kwargs)
    return decorated_function
