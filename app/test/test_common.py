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

from common.convert import *

class TestCommon(unittest.TestCase):
    def setUpClass():
        logging.basicConfig(level=logging.DEBUG)

    def setUp(self):
        self.logger = logging.getLogger()

    def test_toQuotedStr(self):
        self.assertEqual(toQuotedStr(["24", "45", "Ab"]), '"24","45","Ab"')
        self.assertEqual(toQuotedStr([24, 45, Decimal('13.4')]), '"24","45","13.4"')

    def test_toQuoteSafeStr(self):
        self.assertEqual(toQuoteSafeStr('ab"cd"ef'), 'ab\\"cd\\"ef')

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


