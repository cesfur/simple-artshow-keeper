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
import flask
        
def getParameter(key):
    """Get parameter searching through following locations in the following order:
    1) POST arguments
    2) files
    3) GET arguments
    4) COOKIE (Flask Session)
    Args:
        key(string) - Key.
    Returns:
        Found value or None
    """
    key = str(key)
    value = flask.request.form.get(key, None)
    if value is None:
        value = flask.request.files.get(key, None)
        if value is None:
            value = flask.request.args.get(key, None)
            if value is None:
                value = flask.session.get(key, None)
    return value

def persistParameter(key, value):
    flask.session[key] = value
    
def clearPersistetParameter(key):
    if key in flask.session:
        del flask.session[key]
