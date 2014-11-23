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
import os
import flask
import jinja2
from . translate import translateXhtml

def makeXmlResponse(xml):
    response = flask.make_response(xml)
    response.headers['Content-type'] = 'text/xml'
    return response

def respondTranslatedXhtml(name, group, language, parameters=None):
    """Rendered XHTML is post-processed at the server.
    This processing replaces content of every attributes 'value' and 'title' and elements
    whose content begins with '__' with a text retrieved from a translation XML.
    If the message is not found, the original content is stripped of '__' and
    it is used as the content.

    Example:
    Text '__Some Text' searched for a message with id 'Some Text'.

    Returns:
        response or None.
    """
    try:
        if group is not None and len(group) > 0:
            filePath = '{0}.{1}.xhtml'.format(name, group)
        else:
            filePath = '{0}.xhtml'.format(name)

        return makeXmlResponse(translateXhtml(language, flask.render_template(
                filePath,
                language=language,
                **(parameters or {}))))
                
    except jinja2.exceptions.TemplateNotFound:
        return None

def respondLanguageSpecificHtml(name, group, language, parameters=None):
    try:
        if group is not None:
            filePath = '{0}.{1}.{2}.html'.format(name, group, language)
        else:
            filePath = '{0}.{1}.html'.format(name, language)
        return flask.render_template(filePath, language=language, **(parameters or {}))
    except jinja2.exceptions.TemplateNotFound:
        return None

def respondHtml(name, group, language, parameters=None):
    response = respondTranslatedXhtml(name, group, language, parameters)
    if response is not None:
        return response

    response = respondLanguageSpecificHtml(name, group, language, parameters)
    if response is not None:
        return response

    if group is not None:
        # Try output which does not depend on the user group.
        response = respondTranslatedXhtml(name, None, language, parameters)
        if response is not None:
            return response

        response = respondLanguageSpecificHtml(name, None, language, parameters)
        if response is not None:
            return response

    flask.abort(404)

def respondXml(name, group, language, parameters=None):
    filePath = '{0}.{1}.{2}.xml'.format(name, group, language)
    return makeXmlResponse(flask.render_template(filePath, language=language, **(parameters or {})))
