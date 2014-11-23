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
import xml.dom
from xml.dom import minidom

class PhraseDictionary:
    def __init__(self, logger, filename=None):
        self.__ROOT_ELEMENT = "dictionary"
        self.__PHRASE_ELEMENT = "phrase"
        self.__PHRASE_ID_ATRIBUTE = "id"
        self.__logger = logger
        self.__phrases = {}

        if filename is not None:
            self.load(filename)

    def load(self, filename):
        self.__phrases = {}
        try:
            xmldoc = minidom.parse(filename)
        except FileNotFoundError:
            self.__logger.warning(
                    'Phrase dictionary "{0}" not found.'.format(
                        self.__filename, len(self.__rows)))
        else:            
            if xmldoc.documentElement.localName != self.__ROOT_ELEMENT:
                self.__logger.error(
                        'Root "{0}" of document "{1}" does not match expected root "{2}"'.format(
                            xmldoc.documentElement.localName, filename, self.__ROOT_ELEMENT))
            else:
                for element in xmldoc.documentElement.childNodes:
                    if element.nodeType == xml.dom.Node.ELEMENT_NODE and \
                            element.localName == self.__PHRASE_ELEMENT and \
                            self.__PHRASE_ID_ATRIBUTE in element.attributes:

                        id = element.attributes[self.__PHRASE_ID_ATRIBUTE].nodeValue
                        try:
                            phrase = next(textElement.nodeValue for textElement in element.childNodes if textElement.nodeType == xml.dom.Node.TEXT_NODE)
                        except StopIteration:
                            phrase = ''
                        self.__phrases[id] = phrase
                        self.__logger.debug('Added a phrase [{0}] "{1}"'.format(id, phrase))
                self.__logger.info('Loaded {0} phrases'.format(len(self.__phrases)))

    def count(self):
        return len(self.__phrases)

    def get(self, id):
        return self.__phrases.get(id, id)

    def add(self, id, phrase):
        self.__phrases[id] = phrase
