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
import logging
import string
import xml.dom
from xml.dom import minidom

__phraseDictionaries = {}

def registerDictionary(language, dictionary):
    global __phraseDictionaries
    __phraseDictionaries[language] = dictionary

def translateString(language, string):
    global __phraseDictionaries

    if string.startswith('__'):
        string = string[2:]
        dictionary = __phraseDictionaries.get(language, None)
        if dictionary is not None:
            string = dictionary.get(string)
    return string

def translateXhtmlAttribute(language, element, attributeName):
    attribute = element.attributes.get(attributeName, None)
    if attribute is not None:
        attribute.nodeValue = translateString(language, attribute.nodeValue)

def translateXhtmlElement(language, element):
    translateXhtmlAttribute(language, element, 'value')
    translateXhtmlAttribute(language, element, 'title')

    for node in element.childNodes:
        if node.nodeType == minidom.Node.ELEMENT_NODE:
            translateXhtmlElement(language, node)
        elif node.nodeType == minidom.Node.TEXT_NODE:
            node.nodeValue = translateString(language, node.nodeValue)

def translateXhtml(language, xml):
    try:
        xmldoc = xml if isinstance(xml, minidom.Document) else minidom.parseString(xml)
        translateXhtmlElement(language, xmldoc.documentElement)
        return xmldoc if isinstance(xml, minidom.Document) else xmldoc.toxml(encoding=xmldoc.encoding)
    except:
        logging.getLogger('translate').error(u'XML: {0}'.format(xml.encode('ascii', 'ignore')))
        raise

