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
import unittest
import logging
import sys
import os
import decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from . datafile import Datafile
from common.convert import *
from common.translate import *
from common.phrase_dictionary import *
from common.authentication import *

class TestCommon(unittest.TestCase):
    def setUpClass():
        logging.basicConfig(level=logging.DEBUG)

    def setUp(self):
        self.logger = logging.getLogger()

        self.phraseDictionaryFile = Datafile('test.common.phrase_dictionary.xml', self.id())

    def tearDown(self):
        self.phraseDictionaryFile.clear()

    def test_toNonEmptyStr(self):
        self.assertIsNone(toNonEmptyStr(None))
        self.assertIsNone(toNonEmptyStr(''))
        self.assertEqual('Tiger', toNonEmptyStr('Tiger'))
        self.assertEqual('123', toNonEmptyStr('123'))

    def test_toQuotedStr(self):
        self.assertEqual(toQuotedStr(["24", "45", "Ab"]), '"24","45","Ab"')
        self.assertEqual(toQuotedStr([24, 45, Decimal('13.4')]), '"24","45","13.4"')

    def test_toQuoteSafeStr(self):
        self.assertEqual(toQuoteSafeStr('ab"cd"ef'), 'ab\\"cd\\"ef')

    def test_toDecimal(self):
        # Possitive numbers
        self.assertEqual(toDecimal(20), Decimal('20'))
        self.assertEqual(toDecimal('20'), Decimal('20'))
        self.assertEqual(toDecimal(20.125), Decimal('20.125'))
        self.assertEqual(toDecimal('20.125'), Decimal('20.125'))

        # Negative numbers
        self.assertEqual(toDecimal(-20), Decimal('-20'))
        self.assertEqual(toDecimal('-20'), Decimal('-20'))

        # Zero
        self.assertEqual(toDecimal(0), Decimal('0'))
        self.assertEqual(toDecimal('0.00'), Decimal('0'))
        self.assertEqual(toDecimal('0'), Decimal('0'))

    def test_checkRange(self):
        self.assertEqual(checkRange(23, 1, 100), 23)
        self.assertEqual(checkRange(123, 1, None), 123)
        self.assertIsNone(checkRange(-1, 1, None))
        self.assertEqual(checkRange(-1, None, 100), -1)
        self.assertIsNone(checkRange(123, None, 100))

    def test_JSONDecimalEncoder(self):
        self.assertEqual(json.dumps(
                {'decimal': Decimal('23.4')},
                cls=JSONDecimalEncoder),
                         '{"decimal": "23.4"}')
        self.assertEqual(json.dumps(
                {'str': 'String'},
                cls=JSONDecimalEncoder),
                         '{"str": "String"}')
        self.assertEqual(json.dumps(
                {'int': 23},
                cls=JSONDecimalEncoder),
                         '{"int": 23}')

    def test_PhraseDictionary(self):
        phrases = PhraseDictionary(self.logger, self.phraseDictionaryFile.getFilename())
        self.assertEqual(17, phrases.count())
        self.assertEqual('Stav pokladny', phrases.get('Cash Drawer Info'))
        self.assertEqual('Unknown String', phrases.get('Unknown String'))

        phrases.add('String', 'Added String')
        self.assertEqual(18, phrases.count())
        self.assertEqual('Added String', phrases.get('String'))

    def test_translateString(self):
        # Setup and register dictionary.
        LANGUAGE = 'en'
        OTHER_LANGUAGE = 'cz'
        phrases = PhraseDictionary(self.logger)
        phrases.add('String 1', 'Translated 1')
        phrases.add('String 2', 'Translated 2')
        registerDictionary(LANGUAGE, phrases)

        # No translated string

        # Single string
        self.assertEqual('Nothing to translate', translateString(LANGUAGE, 'Nothing to translate'))
        self.assertEqual('Translated 2', translateString(LANGUAGE, '__String 2'))
        self.assertEqual('Translated 2', translateString(LANGUAGE, '__String 2__'))
        self.assertEqual('String 2', translateString(OTHER_LANGUAGE, '__String 2'))
        self.assertEqual('NotFound', translateString(LANGUAGE, '__NotFound'))

        # String with tail
        self.assertEqual('Translated 2 is here', translateString(LANGUAGE, '__String 2__ is here'))
        self.assertEqual('NotFound is gone', translateString(LANGUAGE, '__NotFound__ is gone'))

        # String with prefix
        self.assertEqual('Here is Translated 2', translateString(LANGUAGE, 'Here is __String 2'))
        self.assertEqual('Here is Translated 1', translateString(LANGUAGE, 'Here is __String 1__'))
        self.assertEqual('Go with NotFound', translateString(LANGUAGE, 'Go with __NotFound'))

        # String in the middle
        self.assertEqual('Then, Translated 2 happend.', translateString(LANGUAGE, 'Then, __String 2__ happend.'))
        self.assertEqual('Then, Not Found happend.', translateString(LANGUAGE, 'Then, __Not Found__ happend.'))

        # Multiple strings
        self.assertEqual('Then, Translated 2 and Not Found happend.', translateString(LANGUAGE, 'Then, __String 2__ and __Not Found__ happend.'))
        self.assertEqual('Then, Translated 2Not Found happend.', translateString(LANGUAGE, 'Then, __String 2____Not Found__ happend.'))

        # Errors
        self.assertEqual('', translateString(LANGUAGE, '__'))
        self.assertEqual('', translateString(LANGUAGE, '____'))


    def test_translateXhtml(self):
        # Setup and register dictionary.
        LANGUAGE = 'en'
        phrases = PhraseDictionary(self.logger)
        phrases.add('String 1', 'Translated String 1')
        phrases.add('String 2', 'Translated String 2')
        registerDictionary(LANGUAGE, phrases)

        # Prepare HTML
        xml = '''<?xml version="1.0" ?>
        <html>
            <body>
                <!-- Comment -->
                <h1>Not translated</h1>
                <p>__String not found</p>
                <p>__String 1</p>
                <form>
                    <input value="__String not found"/>
                    <input value="__String 2" title="__String not found"/>
                </form>
            </body>
        </html>'''
        expectedXml = '''<?xml version="1.0" ?><html>
            <body>
                <!-- Comment -->
                <h1>Not translated</h1>
                <p>String not found</p>
                <p>Translated String 1</p>
                <form>
                    <input value="String not found"/>
                    <input title="String not found" value="Translated String 2"/>
                </form>
            </body>
        </html>'''
        translatedXml = translateXhtml(LANGUAGE, xml)
        print(translatedXml)
        self.assertEqual(expectedXml, translatedXml)

    def test_getRandom(self):
        # This test is not valid because it test justs a few cases
        pile = {}
        for i in range(65536):
            number = getNonZeroRandom()
            self.assertNotEqual(number, 0)
            self.assertIsNone(pile.get(number))
            pile[number] = True
