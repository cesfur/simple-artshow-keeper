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
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from artshowkeeper.model.currency import CurrencyField
from artshowkeeper.controller.format import *

class TestController(unittest.TestCase):
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)

    def setUp(self):
        self.logger = logging.getLogger()

    def test_formatNumber(self):
        self.assertEqual(formatNumber(Decimal('-235.678'), 0, 'cz'), '-236')

        self.assertEqual(formatNumber(Decimal('1235.678'), 0, 'cz'), '1 236')
        self.assertEqual(formatNumber(Decimal('1235.678'), 4, 'cz'), '1 235,6780')

        self.assertEqual(formatNumber(Decimal('1234.456'), 2, 'cz'), '1 234,46')
        self.assertEqual(formatNumber(Decimal('1234.456'), 2, 'en'), '1,234.46')
        self.assertEqual(formatNumber(Decimal('1234.456'), 2, 'de'), '1.234,46')
        self.assertEqual(formatNumber(Decimal('1234.456'), 2, 'xx'), '1234.46')

    def test_formatCurrency(self):
        currencyAmount = {
                CurrencyField.FORMAT_PREFIX: 'D ',
                CurrencyField.AMOUNT: Decimal('1234.56'),
                CurrencyField.DECIMAL_PLACES: 0,
                CurrencyField.FORMAT_SUFFIX: ' E'}
        self.assertEqual(formatCurrency(currencyAmount, 'cz'), 'D 1 235 E')

        currencyAmount = {
                CurrencyField.FORMAT_PREFIX: '$',
                CurrencyField.AMOUNT: Decimal('48.2'),
                CurrencyField.DECIMAL_PLACES: 2,
                CurrencyField.FORMAT_SUFFIX: ''}
        self.assertEqual(formatCurrency(currencyAmount, 'cz'), '$48,20')

    def test_formatItem(self):
        # formatting of an empty item
        self.assertIsNone(formatItem(None, 'xx'))

        # formatting of an item
        item = {
                ItemField.INITIAL_AMOUNT_IN_CURRENCY: [
                        {
                                CurrencyField.FORMAT_PREFIX: 'D ',
                                CurrencyField.AMOUNT: Decimal(1234),
                                CurrencyField.DECIMAL_PLACES: 0,
                                CurrencyField.FORMAT_SUFFIX: ' E'},
                        {
                                CurrencyField.FORMAT_PREFIX: 'H ',
                                CurrencyField.AMOUNT: Decimal(5678),
                                CurrencyField.DECIMAL_PLACES: 2,
                                CurrencyField.FORMAT_SUFFIX: ' J'}],
                ItemField.AMOUNT_IN_CURRENCY: [],
               } # missing ItemField.AMOUNT_IN_AUCTION_IN_CURRENCY

        item = formatItem(item, 'xx')

        formatted = item[ItemField.FORMATTED]
        self.assertListEqual(['D 1234 E', 'H 5678.00 J'], formatted[ItemField.INITIAL_AMOUNT_IN_CURRENCY])
        self.assertListEqual([], formatted[ItemField.AMOUNT_IN_CURRENCY])
        self.assertTrue(ItemField.AMOUNT_IN_AUCTION_IN_CURRENCY not in formatted)
                    