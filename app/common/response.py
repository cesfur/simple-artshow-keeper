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
import logging
from xml.dom import minidom
from . translate import translateXhtml

def makeXmlResponse(xml):
    response = flask.make_response(xml)
    response.headers['Content-type'] = 'text/xml'
    response.headers['Cache-Control'] = 'no-cache'
    return response

def enhanceXhtml(xmldoc):
    headElement = xmldoc.getElementsByTagName('head')
    if len(headElement) > 0:
        renderMetaElement = xmldoc.createElement('meta')
        renderMetaElement.setAttribute('name', 'viewport')
        renderMetaElement.setAttribute('content', 'width=device-width, initial-scale=1.0')
        headElement[0].appendChild(renderMetaElement)

        encodingMetaElement = xmldoc.createElement('meta')
        encodingMetaElement.setAttribute('charset', 'UTF-8')
        headElement[0].appendChild(encodingMetaElement)

    return xmldoc

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
    xml = None
    try:
        if group is not None and len(group) > 0:
            filePath = '{0}.{1}.xhtml'.format(name, group)
        else:
            filePath = '{0}.xhtml'.format(name)

        xml = flask.render_template(filePath, language=language, **(parameters or {}))
        xml = enhanceXhtml(translateXhtml(language, minidom.parseString(xml))).toxml()
        if xml.startswith('<?xml'):
            index = xml.find('?>')
            if index > 0:
                xml = xml[(index + 2):]
        return makeXmlResponse('<!DOCTYPE html>\n' + xml)
                
    except jinja2.exceptions.TemplateNotFound:
        return None
    except:
        logging.getLogger('response').error(
                u'XML: {0}'.format(
                        xml.encode('ascii', 'ignore') if xml is not None else '<none>'))
        raise


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

def respondSpecificXml(name, group, language, parameters):
    try:
        if name is None or len(str(name)) == 0:
            return None

        # Combine a string 'name.group.language.xml'.
        # Skip components which are None.
        filenameComponents = []
        filenameComponents.append(str(name))
        if group is not None:
            filenameComponents.append(str(group))
        if language is not None:
            filenameComponents.append(str(language))
        filenameComponents.append('xml')

        return makeXmlResponse(flask.render_template(
                '.'.join(filenameComponents),
                language=language,
                **(parameters or {})))
    except jinja2.exceptions.TemplateNotFound:
        return None

def respondXml(name, group, language, parameters=None):
    """Respond with xml. Template file precendence is following:
    1. name.group.language.xml (e.g. getstatus.admin.en.xml)
    2. name.group.xml
    3. name.language.xml
    4. name.xml

    Returns:
        response or failure.
    """
    response = respondSpecificXml(name, group, language, parameters)
    if response is not None:
        return response

    response = respondSpecificXml(name, group, None, parameters)
    if response is not None:
        return response

    response = respondSpecificXml(name, None, language, parameters)
    if response is not None:
        return response

    response = respondSpecificXml(name, None, None, parameters)
    if response is not None:
        return response

    flask.abort(404)

def respondCustomDataFile(customDataDir, dataDir, filename, language):
    """ Respond with custom data file. Assuming that filename is <name><.ext>,
    pick the file based on the following order:
    1. customDataDir/name.ext
    2. dataDir/name.language.ext
    3. dataDir/name.ext

    Returns:
        response or none.
    """
    # try custom folder
    if customDataDir is not None and os.path.exists(os.path.join(customDataDir, filename)):
        return flask.send_from_directory(customDataDir, filename)

    # try language specific version
    if language is not None:
        name, ext = os.path.splitext(filename)
        langFilename = '{0}.{1}{2}'.format(name, language, ext)
        if os.path.exists(os.path.join(dataDir, langFilename)):
            return flask.send_from_directory(dataDir, langFilename)

    # try generic version
    return flask.send_from_directory(dataDir, filename)
