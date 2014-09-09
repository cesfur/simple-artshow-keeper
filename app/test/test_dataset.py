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

from datafile import Datafile
from common.result import Result
from model.dataset import Dataset
from model.item import ItemField, ImportedItemField
from model.currency import CurrencyField

class TestDataset(unittest.TestCase):
    def setUpClass():
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

    def tearDown(self):
        self.itemFile.clear()
        self.sessionFile.clear()
        self.currencyFile.clear()

        del self.dataset
        
    def test_restorePersist(self):
        self.dataset.restore()
        self.dataset.persist()
        self.dataset.restore()

    def test_sessionPairs(self):
        self.dataset.restore()
        sessionID = 1051183055
        
        # read pairs
        pairs = self.dataset.getSessionPairs(sessionID)
        self.assertEqual(len(pairs), 2,
            'Model.Session: Expected session 2 pairs, got: %(pairs)s.' % { 'pairs': str(pairs) })
            
        # update existing pair
        self.dataset.updateSessionPairs(sessionID, AddedItemCodes = sessionID)
        pairs = self.dataset.getSessionPairs(sessionID)
        self.assertTrue('AddedItemCodes' in pairs and pairs['AddedItemCodes'] == sessionID,
            'Model.Session: Updated a pair ''AddedItemCodes'' but got: %(pairs)s.' % { 'pairs': str(pairs) })

        # insert new pair
        self.dataset.updateSessionPairs(sessionID, NewPair = 'NewPair')
        pairs = self.dataset.getSessionPairs(sessionID)
        self.assertTrue(len(pairs) == 3 and 'NewPair' in pairs,
            'Model.Session: Added a pair ''NewPair'' but got: %(pairs)s.' % { 'pairs': str(pairs) })

        # delete a pair
        self.dataset.updateSessionPairs(sessionID, CreatedTimestamp = None)
        pairs = self.dataset.getSessionPairs(sessionID)
        self.assertTrue(len(pairs) == 2 and 'CreatedTimestamp' not in pairs,
            'Model.Session: Deleted a pair ''CreatedTimestamp'' but got: %(pairs)s.' % { 'pairs': str(pairs) })

    def test_sessionValues(self):
        self.dataset.restore()
        sessionID = 1051183055
            
        # read existing value
        value = self.dataset.getSessionValue(sessionID, 'CreatedTimestamp')
        self.assertEqual(value, '2014-02-16 14:27:16.460836',
            'Model.Session.Value: Expected value ''2014-02-16 14:27:16.460836'' of a key ''CreatedTimestamp'', got: %(value)s.' % { 'value': str(value) })

        # read non-existing value
        value = self.dataset.getSessionValue(sessionID, 'NotExisting')
        self.assertEqual(value, None,
            'Model.Session.Value: Reading non-existing key ''NotExisting'' returned a value: %(value)s.' % { 'value': str(value) })

    def test_getItems(self):
        self.dataset.restore()

        # get all items
        items = self.dataset.getItems(None)
        self.assertEqual(len(items), 27)

        # add a new item
        code = self.dataset.getNextItemCode()
        self.assertTrue(self.dataset.addItem(
                code=code,
                owner=34,
                title='Clever Bull',
                author='Redfox',
                medium='Pencil',
                state='OTHER',
                initialAmount='12.3',
                charity='43',
                note=None))

        # get new item and verify data types
        item = self.dataset.getItem(code)
        self.assertTrue(isinstance(item[ItemField.OWNER], int))
        self.assertTrue(isinstance(item[ItemField.CHARITY], int))
        self.assertTrue(isinstance(item[ItemField.INITIAL_AMOUNT], Decimal))
        self.assertTrue(isinstance(item[ItemField.TITLE], str))
        self.assertTrue(isinstance(item[ItemField.AUTHOR], str))
        self.assertTrue(isinstance(item[ItemField.STATE], str))
        self.assertTrue(isinstance(item[ItemField.CODE], str))
        self.assertTrue(isinstance(item[ItemField.MEDIUM], str))
        self.assertIsNone(item[ItemField.NOTE])

        # get all items again and see whether we have added just one item
        # i.e. the reserved item is not present
        items = self.dataset.getItems(None)
        self.assertEqual(len(items), 28)


    def test_getUpdateItem(self):
        self.dataset.restore()

        # Get existing item
        item = self.dataset.getItem('A3')
        self.assertNotEqual(item, None)

        # Update title
        newTitle = 'ABCDEFGH'
        item[ItemField.TITLE] = newTitle
        self.assertTrue(self.dataset.updateItem('A3', **item))
        items = self.dataset.getItems('Title=="{0}"'.format(newTitle))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0][ItemField.CODE], 'A3')

        # Update buyer
        newBuyer = 9999
        self.assertTrue(self.dataset.updateItem('A3', **{ItemField.BUYER: newBuyer}))
        items = self.dataset.getItems('Buyer=="{0}"'.format(newBuyer))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0][ItemField.CODE], 'A3')

    def test_getNextItemCode(self):
        self.dataset.restore()

        # Create new top based on dataset
        code = self.dataset.getNextItemCode()
        self.assertEqual(code, '57')

        # Advance
        code = self.dataset.getNextItemCode()
        self.assertEqual(code, '58')
        code = self.dataset.getNextItemCode()
        self.assertEqual(code, '59')

    def test_readImportLine(self):
        # Item not for sale.
        result, item = self.dataset.readImportLine('Wolf\tTrees\t\t\n')
        self.assertEqual(result, Result.SUCCESS)
        self.assertDictEqual(item, {
                ImportedItemField.AUTHOR: 'Wolf',
                ImportedItemField.TITLE: 'Trees',
                ImportedItemField.INITIAL_AMOUNT: None,
                ImportedItemField.CHARITY: None })

    def test_getCurrencyInfo(self):
        self.dataset.restore()

        # guarantee that the result matches order of the input
        currencyInfoList = self.dataset.getCurrencyInfo(['czk', 'eur', 'usd'])
        self.assertListEqual(
                ['czk', 'eur', 'usd'],
                [currencyInfo[CurrencyField.CODE] for currencyInfo in currencyInfoList])
        currencyInfoList = self.dataset.getCurrencyInfo(['usd', 'eur', 'czk'])
        self.assertListEqual(
                ['usd', 'eur', 'czk'],
                [currencyInfo[CurrencyField.CODE] for currencyInfo in currencyInfoList])

        # missing currency
        currencyInfoList = self.dataset.getCurrencyInfo(['usd', 'eur', 'xxx'])
        self.assertListEqual(
                ['usd', 'eur', 'xxx'],
                [currencyInfo[CurrencyField.CODE] for currencyInfo in currencyInfoList])

    def test_updateCurrencyInfo(self):
        self.dataset.restore()
        
        # update with valid data and various method of writing the amount
        self.assertEqual(
                Result.SUCCESS,
                self.dataset.updateCurrencyInfo([
                        {
                                CurrencyField.CODE: 'czk',
                                CurrencyField.AMOUNT_IN_PRIMARY: '1.23'},
                        {
                                CurrencyField.CODE: 'eur',
                                CurrencyField.AMOUNT_IN_PRIMARY: 4.56 }]))
        currencyInfoList = self.dataset.getCurrencyInfo(['czk', 'eur', 'usd'])
        self.assertListEqual(
                [Decimal('1.23'), Decimal(4.56), Decimal('19.71')],
                [currencyInfo[CurrencyField.AMOUNT_IN_PRIMARY] for currencyInfo in currencyInfoList])

        # update with invalid data
        self.assertEqual(
                Result.INPUT_ERROR,
                self.dataset.updateCurrencyInfo([
                        {
                                CurrencyField.CODE: 'czk' }]))
        self.assertEqual(
                Result.INPUT_ERROR,
                self.dataset.updateCurrencyInfo([
                        {
                                CurrencyField.AMOUNT_IN_PRIMARY: 4.56 }]))


if __name__ == '__main__':
    unittest.main()
