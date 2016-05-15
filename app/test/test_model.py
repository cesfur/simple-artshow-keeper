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
import io
import codecs
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from . datafile import Datafile
from common.result import Result
from model.model import Model
from model.dataset import Dataset
from model.item import ItemState, ItemField, ImportedItemField
from model.currency import Currency, CurrencyField
from model.summary import SummaryField, Summary, DrawerSummaryField, ActorSummary

class TestModel(unittest.TestCase):
    def setUpClass():
        logging.basicConfig(level=logging.DEBUG)

    def setUp(self):
        self.logger = logging.getLogger()

        self.testFiles = []

        self.itemFile = Datafile('test.model.items.xml', self.id())
        self.itemFileAuctionOnly = Datafile('test.model.items.auction_only.xml', self.id())
        self.sessionFile = Datafile('test.model.session.xml', self.id())
        self.currencyFile = Datafile('test.model.currency.xml', self.id())
        self.importFileCsv = Datafile('test.model.import.csv', self.id())
        self.importFileTxt = Datafile('test.model.import.txt', self.id())

        self.dataset = Dataset(
                self.logger, './',
                self.sessionFile.getFilename(),
                self.itemFile.getFilename(),
                self.currencyFile.getFilename())
        self.dataset.restore()

        self.currency = Currency(
                self.logger,
                self.dataset,
                currencyCodes=['czk', 'eur'])
        self.model = Model(
                self.logger,
                self.dataset,
                self.currency)

    def tearDown(self):
        self.itemFile.clear()
        self.sessionFile.clear()
        self.currencyFile.clear()
        self.importFileCsv.clear()
        self.importFileTxt.clear()
        for file in self.testFiles:
            file.clear()

        del self.model
        del self.currency
        del self.dataset

    def restoreTestFile(self, filename):
        testFile = Datafile(filename, self.id())
        self.testFiles.append(testFile)
        return testFile
        
    def test_getItem(self):
        item = self.model.getItem('A2')
        self.assertDictContainsSubset({ItemField.CODE: 'A2'}, item)
        self.assertListEqual([Decimal('250'), Decimal('9.21')], [currency[CurrencyField.AMOUNT] for currency in item[ItemField.INITIAL_AMOUNT_IN_CURRENCY]])
        self.assertListEqual([Decimal('300'), Decimal('11.06')], [currency[CurrencyField.AMOUNT] for currency in item[ItemField.AMOUNT_IN_CURRENCY]])
        self.assertListEqual([], [currency[CurrencyField.AMOUNT] for currency in item[ItemField.AMOUNT_IN_AUCTION_IN_CURRENCY]])
    
    def test_addNewItem(self):
        sessionID = 11111

        # add (on show)
        self.assertEqual(
                self.model.addNewItem(sessionID, 23, 'Mysteria', 'Wolf', 'Pastel', None, None, None),
                Result.SUCCESS)
        addedItem = self.dataset.getItems('Owner=="23" and Title=="Mysteria" and Author=="Wolf"')[0]
        self.assertDictContainsSubset({
                        ItemField.STATE: ItemState.ON_SHOW,
                        ItemField.MEDIUM: 'Pastel',
                        ItemField.NOTE: None},
                addedItem);

        # duplicate add
        self.assertEqual(
                self.model.addNewItem(sessionID, 23, 'Mysteria', 'Wolf', None, None, None, None),
                Result.DUPLICATE_ITEM)

        # add (on sale) (amount/charity is converted but search expression assumes strings)
        self.assertEqual(
                self.model.addNewItem(sessionID, 35, 'Mysteria', 'Tiger', '', 123.5, 10, 'Good Stuff'),
                Result.SUCCESS)
        addedItem = self.dataset.getItems('Owner=="35" and Title=="Mysteria" and Author=="Tiger" and Charity=="10" and InitialAmount=="123.5"')[0]
        self.assertDictContainsSubset({
                        ItemField.INITIAL_AMOUNT: 123.5,
                        ItemField.CHARITY: 10,
                        ItemField.STATE: ItemState.ON_SALE,
                        ItemField.MEDIUM: None,
                        ItemField.NOTE: 'Good Stuff'},
                addedItem);

        # add (quotes)
        self.assertEqual(
                self.model.addNewItem(sessionID, 98, 'Quotted"Title', 'Qu"es', 'Photo', None, None, 'Do not touch.'),
                Result.SUCCESS)

        # add (empty parameters)
        self.assertEqual(
                self.model.addNewItem(sessionID, 99, 'Strong', 'Lemur', None, None, None, ''),
                Result.SUCCESS)
        addedItem = self.dataset.getItems('Owner=="99" and Title=="Strong" and Author=="Lemur"')[0]
        self.assertDictContainsSubset({
                        ItemField.MEDIUM: None,
                        ItemField.NOTE: None},
                addedItem);

        # add item from an import
        importNumber = 100
        self.assertEqual(
                self.model.addNewItem(sessionID, 99, 'Shy', 'Lemur', None, None, None, '', importNumber),
                Result.SUCCESS)
        addedItem = self.dataset.getItems('Owner=="99" and Title=="Shy" and Author=="Lemur"')[0]
        self.assertDictContainsSubset({
                        ItemField.CODE: str(importNumber),
                        ItemField.IMPORT_NUMBER: importNumber},
                addedItem);

        # add updated item (differs in amount/charity)
        self.assertEqual(
                self.model.addNewItem(sessionID, 99, 'Shy', 'Lemur', None, '12.5', 100, 'Some note', importNumber),
                Result.DUPLICATE_IMPORT_NUMBER)

        # add updated item (differs in name)
        self.assertEqual(
                self.model.addNewItem(sessionID, 99, 'Smiling', 'Lemur', None, None, None, 'Some note', importNumber),
                Result.DUPLICATE_IMPORT_NUMBER)

        # add item from an import with a and import number that matches an existing code
        importNumber = 3
        self.assertEqual(len(self.dataset.getItems('Code=="{0}"'.format(importNumber))), 0)
        self.assertEqual(
                self.model.addNewItem(sessionID, 99, 'Funny', 'Cat', None, None, None, '', importNumber),
                Result.SUCCESS_BUT_IMPORT_RENUMBERED)
        addedItem = self.dataset.getItems('Owner=="99" and Title=="Funny" and Author=="Cat"')[0]
        self.assertDictContainsSubset({
                        ItemField.IMPORT_NUMBER: importNumber},
                addedItem);

        # added list
        addedItemCodes = self.model.getAdded(sessionID)
        self.assertEqual(len(addedItemCodes), 6);


    def test_getAddedItems(self):
        sessionID = 11111

        # add items
        self.assertEqual(self.model.addNewItem(sessionID, 23, 'Mysteria', 'Wolf', 'Oil', None, None, None), Result.SUCCESS)
        self.assertEqual(self.model.addNewItem(sessionID, 35, 'Mysteria', 'Tiger', 'Pencil', '123', '10', None), Result.SUCCESS)

        # get added items
        addedItems = self.model.getAddedItems(sessionID)

        self.assertEqual(len(addedItems), 2);
        item = [item for item in addedItems if item[ItemField.OWNER] == 23][0]
        self.assertListEqual([], [currencyAmount[CurrencyField.AMOUNT] for currencyAmount in item[ItemField.INITIAL_AMOUNT_IN_CURRENCY]])
        item = [item for item in addedItems if item[ItemField.OWNER] == 35][0]
        self.assertListEqual(
                [Decimal('123'), Decimal('4.53')],
                [currencyAmount[CurrencyField.AMOUNT] for currencyAmount in item[ItemField.INITIAL_AMOUNT_IN_CURRENCY]])


    def test_updateItem(self):
        # update item
        self.assertEqual(
                self.model.updateItem(56,
                    owner=1, title='Wolf', author='Greenwolf', medium='Color Pencils', state=ItemState.ON_SALE, 
                    initialAmount='105', charity='50', amount=None, buyer=None, note=None),
                Result.SUCCESS)
        updatedItem = self.dataset.getItems('Owner=="1" and Title=="Wolf" and Author=="Greenwolf" and Medium=="Color Pencils"')[0]
        self.assertDictContainsSubset({
                        ItemField.STATE: ItemState.ON_SALE,
                        ItemField.INITIAL_AMOUNT: 105,
                        ItemField.CHARITY: 50,
                        ItemField.AMOUNT: None,
                        ItemField.NOTE: None},
                updatedItem);        
        self.assertIsNone(updatedItem[ItemField.AMOUNT]);
        self.assertIsNone(updatedItem[ItemField.BUYER]);

        # update item (range error of charity)
        self.assertEqual(
                self.model.updateItem(56,
                    owner=1, title='Wolf', author='Greenwolf', medium='Color Pencils', state=ItemState.FINISHED,
                    initialAmount='105', charity='150', amount='200', buyer='20', note=None),
                Result.INVALID_VALUE)

        # update item (consistency error)
        self.assertEqual(
                self.model.updateItem(56,
                    owner=1, title='Wolf', author='Greenwolf', medium='Color Pencils', state=ItemState.FINISHED,
                    initialAmount='105', charity='10', amount=None, buyer=None, note=None),
                Result.AMOUNT_NOT_DEFINED)

    def test_deleteItems(self):
        # 1. Delete item
        self.assertEqual(self.model.deleteItems(['A11', 'A2', 'A999']), 2)
        self.assertIsNone(self.model.getItem('A11'));
        self.assertIsNone(self.model.getItem('A2'));
        self.assertIsNone(self.model.getItem('A999'));

    def test_getItemNetAmount(self):
        item = self.model.getItem('A2')
        amountNet, amountCharity = self.model.getItemNetAmount(item)
        self.assertEqual(amountNet, Decimal('270'))
        self.assertEqual(amountCharity, Decimal('30'))
        
    def test_getPotentialCharityAmount(self):
        charityAmount = self.model.getPotentialCharityAmount()
        self.assertEqual(charityAmount, Decimal('299'))

    def test_getBadgeReconciliationSummary(self):
        # Owner that has no delivered item
        self.logger.info('Badge 1')
        summary = self.model.getBadgeReconciliationSummary(1)
        self.assertEqual(summary[SummaryField.GROSS_SALE_AMOUNT], Decimal('0'))
        self.assertEqual(summary[SummaryField.CHARITY_DEDUCTION], Decimal('0'))
        self.assertEqual(summary[SummaryField.BOUGHT_ITEMS_AMOUNT], Decimal('350'))
        self.assertEqual(summary[SummaryField.TOTAL_DUE_AMOUNT], Decimal('350'))
        self.assertEqual(len(summary[SummaryField.AVAILABLE_UNSOLD_ITEMS]), 2)
        self.assertEqual(len(summary[SummaryField.AVAILABLE_BOUGHT_ITEMS]), 2)
        self.assertEqual(len(summary[SummaryField.PENDING_SOLD_ITEMS]), 2)
        self.assertEqual(len(summary[SummaryField.DELIVERED_SOLD_ITEMS]), 0)

        # Owner that has just delivered items
        self.logger.info('Badge 2')
        summary = self.model.getBadgeReconciliationSummary(2)
        self.assertEqual(summary[SummaryField.GROSS_SALE_AMOUNT], Decimal('447'))
        self.assertEqual(summary[SummaryField.CHARITY_DEDUCTION], Decimal('49'))
        self.assertEqual(summary[SummaryField.BOUGHT_ITEMS_AMOUNT], Decimal('0'))
        self.assertEqual(summary[SummaryField.TOTAL_DUE_AMOUNT], Decimal('-398'))
        self.assertEqual(len(summary[SummaryField.AVAILABLE_UNSOLD_ITEMS]), 0)
        self.assertEqual(len(summary[SummaryField.AVAILABLE_BOUGHT_ITEMS]), 0)
        self.assertEqual(len(summary[SummaryField.PENDING_SOLD_ITEMS]), 3)
        self.assertEqual(len(summary[SummaryField.DELIVERED_SOLD_ITEMS]), 2)

        # Owner that has delivered items and bought items
        self.logger.info('Badge 4')
        summary = self.model.getBadgeReconciliationSummary(4)
        self.assertEqual(summary[SummaryField.GROSS_SALE_AMOUNT], Decimal('235'))
        self.assertEqual(summary[SummaryField.CHARITY_DEDUCTION], Decimal('36'))
        self.assertEqual(summary[SummaryField.BOUGHT_ITEMS_AMOUNT], Decimal('57'))
        self.assertEqual(summary[SummaryField.TOTAL_DUE_AMOUNT], Decimal('-142'))
        self.assertEqual(len(summary[SummaryField.AVAILABLE_UNSOLD_ITEMS]), 0)
        self.assertEqual(len(summary[SummaryField.AVAILABLE_BOUGHT_ITEMS]), 1)
        self.assertEqual(len(summary[SummaryField.PENDING_SOLD_ITEMS]), 0)
        self.assertEqual(len(summary[SummaryField.DELIVERED_SOLD_ITEMS]), 2)

        # Owner that has items either finished, not delivered, or unsold
        self.logger.info('Badge 6')
        summary = self.model.getBadgeReconciliationSummary(6)
        self.assertEqual(summary[SummaryField.GROSS_SALE_AMOUNT], Decimal('0'))
        self.assertEqual(summary[SummaryField.CHARITY_DEDUCTION], Decimal('0'))
        self.assertEqual(summary[SummaryField.BOUGHT_ITEMS_AMOUNT], Decimal('0'))
        self.assertEqual(summary[SummaryField.TOTAL_DUE_AMOUNT], Decimal('0'))
        self.assertEqual(len(summary[SummaryField.AVAILABLE_UNSOLD_ITEMS]), 1)
        self.assertEqual(len(summary[SummaryField.AVAILABLE_BOUGHT_ITEMS]), 0)
        self.assertEqual(len(summary[SummaryField.PENDING_SOLD_ITEMS]), 0)
        self.assertEqual(len(summary[SummaryField.DELIVERED_SOLD_ITEMS]), 0)

        # Buyer that has just bought items and some of the bought items are finished
        self.logger.info('Badge 11')
        summary = self.model.getBadgeReconciliationSummary(11)
        self.assertEqual(summary[SummaryField.GROSS_SALE_AMOUNT], Decimal('0'))
        self.assertEqual(summary[SummaryField.CHARITY_DEDUCTION], Decimal('0'))
        self.assertEqual(summary[SummaryField.BOUGHT_ITEMS_AMOUNT], Decimal('429'))
        self.assertEqual(summary[SummaryField.TOTAL_DUE_AMOUNT], Decimal('429'))
        self.assertEqual(len(summary[SummaryField.AVAILABLE_UNSOLD_ITEMS]), 0)
        self.assertEqual(len(summary[SummaryField.AVAILABLE_BOUGHT_ITEMS]), 3)
        self.assertEqual(len(summary[SummaryField.PENDING_SOLD_ITEMS]), 0)
        self.assertEqual(len(summary[SummaryField.DELIVERED_SOLD_ITEMS]), 0)

        # Buyer that has items either in auction or finished
        self.logger.info('Badge 12')
        summary = self.model.getBadgeReconciliationSummary(12)
        self.assertEqual(summary[SummaryField.GROSS_SALE_AMOUNT], Decimal('0'))
        self.assertEqual(summary[SummaryField.CHARITY_DEDUCTION], Decimal('0'))
        self.assertEqual(summary[SummaryField.BOUGHT_ITEMS_AMOUNT], Decimal('0'))
        self.assertEqual(summary[SummaryField.TOTAL_DUE_AMOUNT], Decimal('0'))
        self.assertEqual(len(summary[SummaryField.AVAILABLE_UNSOLD_ITEMS]), 0)
        self.assertEqual(len(summary[SummaryField.AVAILABLE_BOUGHT_ITEMS]), 0)
        self.assertEqual(len(summary[SummaryField.PENDING_SOLD_ITEMS]), 0)
        self.assertEqual(len(summary[SummaryField.DELIVERED_SOLD_ITEMS]), 0)

    def test_reconciliateBadge(self):
        # Badge 1 contains:
        # * sold item which has not been paid for (code: A2)
        # * self-sale of an item (code: 56)
        summaryBefore = self.model.getBadgeReconciliationSummary(1)
        self.assertTrue(self.model.reconciliateBadge(1))
        summaryAfter = self.model.getBadgeReconciliationSummary(1)
        self.assertEqual(summaryAfter[SummaryField.GROSS_SALE_AMOUNT], Decimal('200'))
        self.assertEqual(summaryAfter[SummaryField.CHARITY_DEDUCTION], Decimal('20'))
        self.assertEqual(summaryAfter[SummaryField.BOUGHT_ITEMS_AMOUNT], Decimal('0'))
        self.assertEqual(summaryAfter[SummaryField.TOTAL_DUE_AMOUNT], Decimal('-180'))
        self.assertListEqual(
            [],
            summaryAfter[SummaryField.AVAILABLE_UNSOLD_ITEMS])
        self.assertListEqual(
            [],
            summaryAfter[SummaryField.AVAILABLE_BOUGHT_ITEMS])
        self.assertListEqual(
            ['A2'],
            [item[ItemField.CODE] for item in summaryAfter[SummaryField.PENDING_SOLD_ITEMS]])
        self.assertListEqual(
            ['56'],
            [item[ItemField.CODE] for item in summaryAfter[SummaryField.DELIVERED_SOLD_ITEMS]])
    
        for itemUnsoldBefore in summaryBefore[SummaryField.AVAILABLE_UNSOLD_ITEMS]:
            self.assertEqual(
                    self.model.getItem(itemUnsoldBefore[ItemField.CODE])[ItemField.STATE],
                    ItemState.FINISHED,
                    'Item {0}'.format(itemUnsoldBefore[ItemField.CODE]))

        for itemBoughtBefore in summaryBefore[SummaryField.AVAILABLE_BOUGHT_ITEMS]:
            self.assertEqual(
                    self.model.getItem(itemBoughtBefore[ItemField.CODE])[ItemField.STATE],
                    ItemState.DELIVERED,
                    'Item {0}'.format(itemBoughtBefore[ItemField.CODE]))

        for itemDeliveredBefore in summaryBefore[SummaryField.DELIVERED_SOLD_ITEMS]:
            self.assertEqual(
                    self.model.getItem(itemDeliveredBefore[ItemField.CODE])[ItemField.STATE],
                    ItemState.FINISHED,
                    'Item {0}'.format(itemDeliveredBefore[ItemField.CODE]))


    def test_summaryChecksum(self):
        summaryA = self.model.getBadgeReconciliationSummary(1)
        summaryB = self.model.getBadgeReconciliationSummary(11)
        self.assertNotEqual(Summary.calculateChecksum(summaryA), Summary.calculateChecksum(summaryB))

    def test_getCashDrawerSummary(self):
        summary = self.model.getCashDrawerSummary()
        self.assertIsNotNone(summary)
        self.assertEqual(summary[DrawerSummaryField.TOTAL_GROSS_CASH_DRAWER_AMOUNT], Decimal('709'))
        self.assertEqual(summary[DrawerSummaryField.TOTAL_NET_CHARITY_AMOUNT], Decimal('112'))
        self.assertEqual(summary[DrawerSummaryField.TOTAL_NET_AVAILABLE_AMOUNT], Decimal('597'))
        self.assertListEqual(
                sorted([actorSummary.Badge for actorSummary in summary[DrawerSummaryField.BUYERS_TO_BE_CLEARED]]),
                [1, 3, 4, 11, 13])
        self.assertListEqual(
                sorted([actorSummary.Badge for actorSummary in summary[DrawerSummaryField.OWNERS_TO_BE_CLEARED]]),
                [1, 2, 3, 4, 6, 7])
        self.assertEqual(len(summary[DrawerSummaryField.PENDING_ITEMS]), 3)


    def test_importItemsFromCsv(self):
        # 1. Import
        sessionID = 11111
        binaryStream = io.open(self.importFileCsv.getFilename(), mode='rb')
        importedItems, importedChecksum = self.model.importCSVFile(sessionID, binaryStream)
        binaryStream.close()

        # 2. Verify
        self.assertEqual(len(importedItems), 13)
        self.assertEqual(importedItems[0][ImportedItemField.IMPORT_RESULT], Result.SUCCESS)
        self.assertEqual(importedItems[1][ImportedItemField.IMPORT_RESULT], Result.DUPLICATE_ITEM)
        self.assertEqual(importedItems[2][ImportedItemField.IMPORT_RESULT], Result.SUCCESS)
        self.assertEqual(importedItems[3][ImportedItemField.IMPORT_RESULT], Result.SUCCESS)
        self.assertEqual(importedItems[4][ImportedItemField.IMPORT_RESULT], Result.INVALID_CHARITY)
        self.assertEqual(importedItems[5][ImportedItemField.IMPORT_RESULT], Result.INCOMPLETE_SALE_INFO)
        self.assertEqual(importedItems[6][ImportedItemField.IMPORT_RESULT], Result.INVALID_AMOUNT)
        self.assertEqual(importedItems[7][ImportedItemField.IMPORT_RESULT], Result.INVALID_AUTHOR)
        self.assertEqual(importedItems[8][ImportedItemField.IMPORT_RESULT], Result.INVALID_TITLE)
        self.assertEqual(importedItems[9][ImportedItemField.IMPORT_RESULT], Result.DUPLICATE_ITEM)
        self.assertEqual(importedItems[10][ImportedItemField.IMPORT_RESULT], Result.SUCCESS)
        self.assertEqual(importedItems[11][ImportedItemField.IMPORT_RESULT], Result.SUCCESS)
        self.assertEqual(importedItems[12][ImportedItemField.IMPORT_RESULT], Result.SUCCESS)

        # 3. Apply
        defaultOwner = 2
        result, skippedItems, renumberedItems = self.model.applyImport(sessionID, importedChecksum, defaultOwner)
        self.assertEqual(result, Result.SUCCESS)
        self.assertEqual(len(self.model.getAdded(sessionID)), 6)
        self.assertEqual(len(self.dataset.getItems(
                'Owner=="{0}" and Title=="Smooth \\\"Frog\\\"" and Author=="Greentiger" and State=="{1}" and InitialAmount=="120" and Charity=="47"'.format(
                        defaultOwner, ItemState.ON_SALE))), 1)
        self.assertEqual(len(self.dataset.getItems(
                'Owner=="{0}" and Title=="Draft Horse" and Author=="Greentiger" and State=="{1}" and InitialAmount=="500" and Charity=="0"'.format(
                        defaultOwner, ItemState.ON_SALE))), 1)
        self.assertEqual(len(self.dataset.getItems(
                'Owner=="{0}" and Title=="Žluťoučký kůň" and Author=="Greentiger" and State=="{1}"'.format(
                        defaultOwner, ItemState.ON_SHOW))), 1)
        self.assertEqual(len(self.dataset.getItems(
                'Owner=="{0}" and Title=="Eastern Dragon" and Author=="Redwolf" and State=="{1}"'.format(
                        defaultOwner, ItemState.SOLD))), 1)
        self.assertEqual(len(self.dataset.getItems(
                'Owner=="7" and Title=="More Wolves" and Author=="Greenfox" and State=="{0}" and InitialAmount=="280" and Charity=="50"'.format(
                        ItemState.ON_SALE))), 1)

        # 4. Re-apply
        result, skippedItems, renumberedItems = self.model.applyImport(sessionID, importedChecksum, defaultOwner)
        self.assertEqual(result, Result.NO_IMPORT)

        # 5. Re-apply with invalid checksum
        binaryStream = io.open(self.importFileCsv.getFilename(), mode='rb')
        importedItems, importedChecksum = self.model.importCSVFile(sessionID, binaryStream)
        binaryStream.close()
        result, skippedItems, renumberedItems = self.model.applyImport(sessionID, importedChecksum + 50, defaultOwner)
        self.assertEqual(result, Result.INVALID_CHECKSUM)

    def test_importItemsFromCsv_ImportNumberReuse(self):
        # Verify next code. This is crucial for the last test.
        NEXT_AVAILABLE_CODE = 57

        # 1. Import
        importFile = self.restoreTestFile('test.model.import_number.csv');
        sessionID = 11111
        binaryStream = io.open(importFile.getFilename(), mode='rb')
        importedItems, importedChecksum = self.model.importCSVFile(sessionID, binaryStream)
        binaryStream.close()

        # 2. Verify
        self.assertEqual(len(importedItems), 11)
        self.assertEqual(importedItems[0][ImportedItemField.IMPORT_RESULT], Result.SUCCESS)
        self.assertEqual(importedItems[1][ImportedItemField.IMPORT_RESULT], Result.DUPLICATE_ITEM)
        self.assertEqual(importedItems[2][ImportedItemField.IMPORT_RESULT], Result.DUPLICATE_ITEM)
        self.assertEqual(importedItems[3][ImportedItemField.IMPORT_RESULT], Result.DUPLICATE_ITEM)
        self.assertEqual(importedItems[4][ImportedItemField.IMPORT_RESULT], Result.SUCCESS)
        self.assertEqual(importedItems[5][ImportedItemField.IMPORT_RESULT], Result.SUCCESS)
        self.assertEqual(importedItems[6][ImportedItemField.IMPORT_RESULT], Result.SUCCESS)
        self.assertEqual(importedItems[7][ImportedItemField.IMPORT_RESULT], Result.SUCCESS)
        self.assertEqual(importedItems[8][ImportedItemField.IMPORT_RESULT], Result.SUCCESS)
        self.assertEqual(importedItems[9][ImportedItemField.IMPORT_RESULT], Result.SUCCESS)
        self.assertEqual(importedItems[10][ImportedItemField.IMPORT_RESULT], Result.SUCCESS)

        # 3. Apply
        defaultOwner = 2
        result, skippedItems, renumberedItems = self.model.applyImport(sessionID, importedChecksum, defaultOwner)
        self.assertEqual(Result.SUCCESS, result)
        self.assertEqual(7, len(self.model.getAdded(sessionID)))

        # 3a. Check that if Import Number is missing, it will be left empty.
        self.assertDictContainsSubset(
                { ItemField.IMPORT_NUMBER: None },
                self.dataset.getItems('Owner=="7" and Author=="Redpanda" and Title=="Moon cycles"')[0])

        # 3b. Check that a duplicate Import Number in the import was not imported.
        self.assertEqual(
                0,
                len(self.dataset.getItems('Owner=="7" and Author=="Redpanda" and Title=="Fullmoon"')))
        self.assertEqual(
                0,
                len(self.dataset.getItems('Owner=="7" and Author=="Redpanda" and Title=="No moon"')))

        # 3c. Check that an existing item with a matching Import Number has not been updated
        # in case there were changes.
        self.assertEqual(
                1,
                len(self.dataset.getItems('Owner=="7" and Author=="Redpanda" and Title=="Half moon"')))
        updatedItem = self.dataset.getItems('Owner=="7" and Author=="Redpanda" and Title=="Half moon"')[0]
        self.assertIn(updatedItem[ItemField.CODE], self.model.getAdded(sessionID))

        # 3d. Check that an existing item with a matching Import Number has not been updated.
        nonupdatedItem = self.dataset.getItems('Owner=="7" and Author=="Greenfox" and Title=="White Snow"')[0]
        self.assertNotIn(nonupdatedItem[ItemField.CODE], self.model.getAdded(sessionID))

        # 3e. Check that item which import number might have been used earlier is renumbered.
        renumberedItem = self.dataset.getItems('Owner=="7" and Author=="Redpanda" and Title=="Day phases"')[0]
        self.assertNotEqual('45', renumberedItem[ItemField.CODE]);
        self.assertEqual(45, renumberedItem[ItemField.IMPORT_NUMBER]);

        # 3f. Check that Import Number is used case Code if the Code might not have been used previously.
        self.assertDictContainsSubset(
                { ItemField.CODE: '80', ItemField.IMPORT_NUMBER: 80 },
                self.dataset.getItems('Owner=="7" and Author=="Redpanda" and Title=="Morning"')[0])

        self.assertDictContainsSubset(
                { ItemField.CODE: '90', ItemField.IMPORT_NUMBER: 90 },
                self.dataset.getItems('Owner=="7" and Author=="Redpanda" and Title=="Afternoon"')[0])

        # 3g. Check that order of occurance in the import has no impact on ability to use Import Number as Code
        self.assertDictContainsSubset(
                { ItemField.CODE: '85', ItemField.IMPORT_NUMBER: 85 },
                self.dataset.getItems('Owner=="7" and Author=="Redpanda" and Title=="Noon"')[0])

        # 3f. Check that if Import Number might be used as Code at the start of the import, it will be used as Code.
        # No unnumbered or re-numbered item will prevent that.
        self.assertDictContainsSubset(
                { ItemField.CODE: str(NEXT_AVAILABLE_CODE), ItemField.IMPORT_NUMBER: NEXT_AVAILABLE_CODE },
                self.dataset.getItems('Owner=="7" and Author=="Redpanda" and Title=="Day"')[0])


    def test_importItemsFromText(self):
        textStream = io.open(self.importFileTxt.getFilename(), mode='rt', encoding='utf-8')
        text = '\n'.join(textStream.readlines())
        textStream.close()

        # 1. Import
        sessionID = 11111
        importedItems, importedChecksum = self.model.importText(sessionID, text)

        # 2. Verify
        self.assertEqual(len(importedItems), 10)
        self.assertEqual(importedItems[0][ImportedItemField.IMPORT_RESULT], Result.SUCCESS)
        self.assertEqual(importedItems[1][ImportedItemField.IMPORT_RESULT], Result.SUCCESS)
        self.assertEqual(importedItems[2][ImportedItemField.IMPORT_RESULT], Result.INVALID_CHARITY)
        self.assertEqual(importedItems[3][ImportedItemField.IMPORT_RESULT], Result.INCOMPLETE_SALE_INFO)
        self.assertEqual(importedItems[4][ImportedItemField.IMPORT_RESULT], Result.INVALID_AMOUNT)
        self.assertEqual(importedItems[5][ImportedItemField.IMPORT_RESULT], Result.INVALID_AUTHOR)
        self.assertEqual(importedItems[6][ImportedItemField.IMPORT_RESULT], Result.INVALID_TITLE)
        self.assertEqual(importedItems[7][ImportedItemField.IMPORT_RESULT], Result.DUPLICATE_ITEM)
        self.assertEqual(importedItems[8][ImportedItemField.IMPORT_RESULT], Result.DUPLICATE_ITEM)
        self.assertEqual(importedItems[9][ImportedItemField.IMPORT_RESULT], Result.DUPLICATE_ITEM)

        # 3. Apply
        owner = 2
        result, skippedItems, renumberedItems = self.model.applyImport(sessionID, importedChecksum, owner)
        self.assertEqual(result, Result.SUCCESS)
        self.assertEqual(len(self.model.getAdded(sessionID)), 2)
        self.assertEqual(len(self.dataset.getItems(
                'Owner=="{0}" and Title=="Smooth Frog" and Author=="Greentiger" and State=="{1}" and InitialAmount=="120" and Charity=="47"'.format(
                        owner, ItemState.ON_SALE))), 1)
        self.assertEqual(len(self.dataset.getItems(
                'Owner=="{0}" and Title=="Žluťoučký kůň" and Author=="Greentiger" and State=="{1}"'.format(
                        owner, ItemState.ON_SHOW))), 1)
        self.assertEqual(len(self.dataset.getItems(
                'Owner=="{0}" and Title=="Eastern Dragon" and Author=="Redwolf" and State=="{1}"'.format(
                        owner, ItemState.SOLD))), 1)

    def test_getNetAmount(self):
        # Regular amount
        grossAmount = 253
        saleAmount, charityAmount = self.model.getNetAmount(Decimal(grossAmount), 47)
        self.assertEqual((saleAmount, charityAmount), (134, 119))
        self.assertEqual(saleAmount + charityAmount, grossAmount)

        # Excessive amount
        self.assertEqual(self.model.getNetAmount(Decimal('1E+34'), 14), (0, 0))

        # Invalid amount
        self.assertEqual(self.model.getNetAmount(None, 23), (0, 0))

    def test_getSendItemToAuction(self):
        # Item of acceptable state (AUCT)
        item = self.model.sendItemToAuction('A10')
        self.assertIsNotNone(item)
        self.assertDictContainsSubset(
                {
                        ItemField.CODE:'A10',
                        ItemField.AMOUNT_IN_AUCTION:item[ItemField.AMOUNT]},
                self.model.getItemInAuction())
        self.model.clearAuction()
        self.assertIsNone(self.model.getItemInAuction())

        # Item of invalid state (SOLD)
        self.assertIsNone(self.model.sendItemToAuction('A13'))
        self.assertIsNone(self.model.getItemInAuction())

    def test_closeItemAsNotSold(self):
        # Close item
        self.assertEqual(Result.SUCCESS, self.model.closeItemAsNotSold('55'))
        item = self.model.getItem('55')
        self.assertDictContainsSubset(
                {
                        ItemField.STATE: ItemState.NOT_SOLD,
                        ItemField.BUYER: None,
                        ItemField.AMOUNT: None},
                item)

        # Close item which is not closable
        self.assertEqual(Result.ITEM_NOT_CLOSABLE, self.model.closeItemAsNotSold('A13'))

    def test_closeItemAsSold(self):
        # Close item
        self.assertEqual(Result.SUCCESS, self.model.closeItemAsSold('55', Decimal(1000), 9999))
        item = self.dataset.getItems('Buyer=="{0}"'.format(9999))[0]
        self.assertDictContainsSubset(
                {
                        ItemField.STATE: ItemState.SOLD,
                        ItemField.BUYER: 9999,
                        ItemField.AMOUNT: Decimal(1000)},
                item)

        # Close item which is not closable
        self.assertEqual(Result.ITEM_NOT_CLOSABLE, self.model.closeItemAsSold('A13', Decimal(1000), 9999))

    def test_closeItemIntoAuction(self):
        # Close item
        self.assertEqual(Result.SUCCESS, self.model.closeItemIntoAuction('55', Decimal(1000), 9999))
        item = self.dataset.getItems('Buyer=="{0}"'.format(9999))[0]
        self.assertDictContainsSubset(
                {
                        ItemField.STATE: ItemState.IN_AUCTION,
                        ItemField.BUYER: 9999,
                        ItemField.AMOUNT: Decimal(1000)},
                item)

        # Close item which is not closable
        self.assertEqual(Result.ITEM_NOT_CLOSABLE, self.model.closeItemIntoAuction('A13', Decimal(1000), 9999))

    def test_getAllItemsInAuction(self):
        auctionItems = self.model.getAllItemsInAuction()
        self.assertListEqual(
                ['A9', 'A10'],
                [item[ItemField.CODE] for item in auctionItems]);

    def test_getAllItemsInAuction_Ordering(self):
        datasetAuction = Dataset(
                self.logger, './',
                self.sessionFile.getFilename(),
                self.itemFileAuctionOnly.getFilename(),
                self.currencyFile.getFilename())
        datasetAuction.restore()
        modelAuction = Model(
                self.logger,
                datasetAuction,
                self.currency)

        auctionItems = modelAuction.getAllItemsInAuction()
        auctionItems.sort(key=lambda item: item[ItemField.AUCTION_SORT_CODE])

        for item in auctionItems:
            print('{0} - {1}'.format(item[ItemField.AUTHOR], item[ItemField.AMOUNT]))

        # Check that there is no block authors larger than two
        largestBlockSize = 0
        largestBlockAuthor = None
        blockAuthor = None
        blockSize = 0
        for item in auctionItems:
            if blockAuthor is not None and item[ItemField.AUTHOR] == blockAuthor:
                blockSize = blockSize + 1
            else:
                if blockSize > largestBlockSize:
                    largestBlockSize = blockSize
                    largestBlockAuthor = blockAuthor
                blockAuthor = item[ItemField.AUTHOR]
                blockSize = 1
        self.assertGreaterEqual(2, largestBlockSize, 'Author: ' + str(largestBlockAuthor))

if __name__ == '__main__':
    unittest.main()
