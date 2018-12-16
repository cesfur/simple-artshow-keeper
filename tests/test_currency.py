# Artshow Keeper: A support tool for keeping an Artshow running.
# Copyright (C) 2015  Ivo Hanak
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
import io
import codecs
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.datafile import Datafile
from artshowkeeper.common.result import Result
from artshowkeeper.model.dataset import Dataset
from artshowkeeper.model.currency import CurrencyField, Currency

class TestCurrency(unittest.TestCase):
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)

    def setUp(self):
        self.logger = logging.getLogger()

        self.itemFile = Datafile('test.model.items.xml', self.id())
        self.sessionFile = Datafile('test.model.session.xml', self.id())
        self.currencyFile = Datafile('test.model.currency.xml', self.id())

        self.dataset = Dataset(
                self.logger, './',
                self.sessionFile.getFilename(),
                self.itemFile.getFilename(),
                self.currencyFile.getFilename())
        self.dataset.restore()

        self.currency = Currency(
                self.logger,
                self.dataset,
                currencyCodes=['czk', 'eur', 'usd'])

    def tearDown(self):
        self.itemFile.clear()
        self.sessionFile.clear()
        self.currencyFile.clear()

        del self.currency
        del self.dataset

        
    def test_convertToAllCurrencies(self):
        # Valid amount
        amountInCurrency = self.currency.convertToAllCurrencies(154)
        self.assertEqual(len(amountInCurrency), 3)
        self.assertEqual(amountInCurrency[0][CurrencyField.AMOUNT], Decimal('154'))
        self.assertEqual(amountInCurrency[1][CurrencyField.AMOUNT], Decimal('5.68'))
        self.assertEqual(amountInCurrency[2][CurrencyField.AMOUNT], Decimal('7.81'))

        # Valid negative amount
        amountInCurrency = self.currency.convertToAllCurrencies(-154)
        self.assertEqual(len(amountInCurrency), 3)
        self.assertEqual(amountInCurrency[0][CurrencyField.AMOUNT], Decimal('-154'))
        self.assertEqual(amountInCurrency[1][CurrencyField.AMOUNT], Decimal('-5.68'))
        self.assertEqual(amountInCurrency[2][CurrencyField.AMOUNT], Decimal('-7.81'))

        # Excessively large amount that would result to NaN
        amountInCurrency = self.currency.convertToAllCurrencies(Decimal('1E+30'))
        self.assertEqual(len(amountInCurrency), 3)
        self.assertEqual(amountInCurrency[0][CurrencyField.AMOUNT], Decimal('0'))
        self.assertEqual(amountInCurrency[1][CurrencyField.AMOUNT], Decimal('0'))
        self.assertEqual(amountInCurrency[2][CurrencyField.AMOUNT], Decimal('0'))

    def test_updateAmountWithAllCurrencies(self):
        item = {
                    'UNTOUCHABLE': 123,
                    'INPLACE': 100,
                    'OUTPLACE-SRC': 220 }
        self.currency.updateAmountWithAllCurrencies(item, {
                'INPLACE': 'INPLACE',
                'OUTPLACE-SRC': 'OUTPLACE-TGT',
                'UNDEFINED': 'UNDEFINED'})

        # Added fileds OUTPLACE-TGT and UNDEFINED
        self.assertEqual(len(item), 3 + 2)

        self.assertListEqual(item['UNDEFINED'], [])

        self.assertEqual(item['UNTOUCHABLE'], Decimal('123'))

        self.assertEqual(item['INPLACE'][0][CurrencyField.AMOUNT], Decimal('100'))
        self.assertEqual(item['INPLACE'][1][CurrencyField.AMOUNT], Decimal('3.69'))
        self.assertEqual(item['INPLACE'][2][CurrencyField.AMOUNT], Decimal('5.07'))

        self.assertEqual(item['OUTPLACE-SRC'], 220)
        self.assertEqual(item['OUTPLACE-TGT'][0][CurrencyField.AMOUNT], Decimal('220'))
        self.assertEqual(item['OUTPLACE-TGT'][1][CurrencyField.AMOUNT], Decimal('8.11'))
        self.assertEqual(item['OUTPLACE-TGT'][2][CurrencyField.AMOUNT], Decimal('11.16'))


    def test_roundInPrimary(self):
        # Conversion test
        self.assertEqual(self.currency.roundInPrimary('10.543'), Decimal('11'))
        self.assertEqual(self.currency.roundInPrimary(10.543), Decimal('11'))
        self.assertEqual(self.currency.roundInPrimary(Decimal('10.543')), Decimal('11'))
        self.assertEqual(self.currency.roundInPrimary(None), None)
        self.assertEqual(self.currency.roundInPrimary('NUMBER4'), None)

        # Position numbers
        self.assertEqual(self.currency.roundInPrimary(Decimal('10.541')), Decimal('11'))
        self.assertEqual(self.currency.roundInPrimary(Decimal('10.1')), Decimal('10'))
        self.assertEqual(self.currency.roundInPrimary(Decimal('19.995')), Decimal('20'))

        # Negative numbers
        self.assertEqual(self.currency.roundInPrimary(Decimal('-10.541')), Decimal('-11'))

        # Zero
        self.assertEqual(self.currency.roundInPrimary(Decimal('0.00')), Decimal('0'))

if __name__ == '__main__':
    unittest.main()
