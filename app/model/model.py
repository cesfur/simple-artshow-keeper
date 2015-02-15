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
import sys
import logging
import random
import decimal
import io
import json
import csv
from datetime import datetime
from decimal import Decimal

from . import session
from . dataset import Dataset
from . item import ItemField, ItemState, ImportedItemField, calculateImportedItemChecksum
from . currency import Currency, CurrencyField
from . summary import SummaryField, DrawerSummaryField, ActorSummary
from . field_value_error import FieldValueError
from common.convert import *
from common.result import Result

class Model:
    def __init__(self, logger, dataset, currency):
        self.__logger = logger
        self.__dataset = dataset
        self.__currency = currency

    def persist(self):
        self.__dataset.persist()
        
    def startNewSession(self):
        """Start a new session.
        Returns:
            Session ID.
        """
        found = False
        while not found:
            sessionID = int(random.random() * (session.MAX_SESION_ID - 1)) + 1
            if not self.findSession(sessionID):
                self.__logger.info('startNewSession: Created a session {0}'.format(sessionID))
                self.__dataset.updateSessionPairs(sessionID, **{session.Field.CREATED_TIMESTAMP: datetime.now()})

                #TODO: Delete expired sessions (24 hrs?)

                self.__dataset.persist()
                return sessionID
            else:
                self.__logger.debug(
                        'startNewSession: Session {0} is already open, trying a different ID.'.format(sessionID))

    def findSession(self, sessionID):
        """Find a session.
        Args:
            sessionID: Session ID.
        Returns:
            True if the session ID is found.
        """
        return sessionID is not None and self.__dataset.getSessionValue(
                sessionID, session.Field.CREATED_TIMESTAMP, None) is not None

    def clearAdded(self, sessionID):
        """Clear the list of added item codes in a session."""
        self.__dataset.updateSessionPairs(sessionID, **{session.Field.ADDED_ITEM_CODES: None})
    
    def getAdded(self, sessionID):        
        """Retrieve a list of item codes of items added in a session."""
        rawAdded = self.__dataset.getSessionValue(sessionID, session.Field.ADDED_ITEM_CODES, None)
        if rawAdded is not None:
            rawAdded = rawAdded.split(',')
            return [code for code in rawAdded if len(code) > 0]
        else:
            return []

    def getAddedItems(self, sessionID):
        """Retrieve a list of items added in a session.
        Returns:
            A list of items added in the session.
        """
        itemCodes = self.getAdded(sessionID)
        items = []
        for itemCode in itemCodes:
            if len(itemCode) > 0:
                item = self.__dataset.getItem(itemCode)
                if item is not None:
                    items.append(item)
                else:
                    self.__logger.error('getAddedItems: Skipping item ''{0}'' because it has not been found.'.format(itemCode))
        return self.__updateItemAmountCurrency(items)
    
    def setSessionValue(self, sessionID, key, value):
        """Set a pair (key, value) in a session."""
        self.__dataset.updateSessionPairs(sessionID, **{key: value})
        
    def clearSessionValue(self, sessionID, key):
        """Remove a (key, value) in a session."""
        self.__dataset.updateSessionPairs(sessionID, **{key: None})        

    def addNewItem(self, sessionID, owner, title, author, medium, amount, charity, note, importNumber=None):
        """Add a new item.
        Returns:
            Result (class Result).
        """
        ownerRaw = owner
        importNumberRaw = importNumber

        # 1. Evaluate state.
        state = self.__evaluateState(amount, charity)

        # 2. Check validity of the input range.
        owner = toInt(owner)
        if owner is None:
            self.__logger.error('addNewItem: Owner "{0}" is not an integer.'.format(ownerRaw))
            return Result.INPUT_ERROR
        importNumber = toInt(importNumber)
        if importNumberRaw is not None and importNumber is None:
            self.__logger.error('addNewItem: Import Number "{0}" is not an integer.'.format(importNumber))
            return Result.INPUT_ERROR

        if state == ItemState.ON_SALE:
            amount = toDecimal(amount)
            if amount is None or amount < 0:
                self.__logger.error('addNewItem: Amount is not a possitive number.')
                return Result.INPUT_ERROR

            charity = toInt(charity)
            if charity is None or charity < 0 or charity > 100:
                self.__logger.error('addNewItem: Charity is not an integer in a range [0, 100].')
                return Result.INPUT_ERROR
        else:
            amount = None
            charity = None
        
        # 3. Evaluate duplicity.
        if self.__getImportedItem(owner, importNumber) is not None:
            self.__logger.error(
                    'addNewItem: Import item number "{0}" is already defined for owner "{1}".'.format(
                            importNumber, owner))
            return Result.DUPLICATE_IMPORT_NUMBER
        if self.__getSimilarItem(owner, author, title) is not None:
            self.__logger.error('addNewItem: There is a similar item already.')
            return Result.DUPLICATE_ITEM

        # 4. Build a code and insert.
        code = self.__dataset.getNextItemCode()
        if not self.__dataset.addItem(
                    code=code, owner=owner, title=title, author=author, medium=medium,
                    state=state, initialAmount=amount, charity=charity, note=note,
                    importNumber=importNumber):
            self.__logger.error('addNewItem: Adding item "{0}" failed. Item not added.'.format(code))
            return Result.ERROR

        # 5. Update items added in the session
        addedItemCodes = self.__appendAddedCode(sessionID, code)
        self.__logger.info('addNewItem: Added item "{0}" (added codes: {1})'.format(code, addedItemCodes))

        return Result.SUCCESS

    def __evaluateState(self, amount, charity):
        if amount is not None and charity is not None:
            return ItemState.ON_SALE
        else:
            return ItemState.ON_SHOW

    def __appendAddedCode(self, sessionID, code):
        addedItemCodes = self.__dataset.getSessionValue(sessionID, session.Field.ADDED_ITEM_CODES, '')
        addedItemCodes = addedItemCodes + code + ','
        self.__dataset.updateSessionPairs(sessionID, **{session.Field.ADDED_ITEM_CODES: addedItemCodes})
        return addedItemCodes

    def __getImportedItem(self, owner, importNumber):
        item = None
        if owner is not None and importNumber is not None:
            importedItems = self.__dataset.getItems('Owner == "{0}" and ImportNumber == "{1}"'.format(
                owner, importNumber))
            if len(importedItems) > 0:
                item = importedItems[0]
        return item

    def __getSimilarItem(self, owner, author, title):
        similarItems = self.__dataset.getItems(
                'Owner == "{0}" and Author == "{1}" and Title == "{2}"'.format(
                owner, toQuoteSafeStr(author), toQuoteSafeStr(title)))
        if len(similarItems) > 0:
            return similarItems[0]
        else:
            return None

    def dropImport(self, sessionID):
        """Drop import.
        Args:
            sessionID: Session ID.
        """
        self.__dataset.updateSessionPairs(sessionID, **{
                session.Field.IMPORTED_ITEMS: None,
                session.Field.IMPORTED_CHECKSUM: None})

    def __checkImportedItemConsistency(self, importedItem):
        """Check consistency of imported item.
        Returns:
            Import result.
        """
        if importedItem[ImportedItemField.AUTHOR] is None or len(importedItem[ImportedItemField.AUTHOR]) == 0:
            self.__logger.error('__checkImportedItemConsistency: Author is undefined.')
            return Result.INVALID_AUTHOR
        if importedItem[ImportedItemField.TITLE] is None or len(importedItem[ImportedItemField.TITLE]) == 0:
            self.__logger.error('__checkImportedItemConsistency: Title is undefined.')
            return Result.INVALID_TITLE
        if importedItem[ImportedItemField.INITIAL_AMOUNT] is None and importedItem[ImportedItemField.CHARITY] is None:
            return Result.SUCCESS
        if importedItem[ImportedItemField.INITIAL_AMOUNT] is None or importedItem[ImportedItemField.CHARITY] is None:
            self.__logger.error('__checkImportedItemConsistency: Either charity is undefined while initial amount is defined or vice versa.')
            return Result.INCOMPLETE_SALE_INFO
        if toDecimal(importedItem[ImportedItemField.INITIAL_AMOUNT]) < 0:
            self.__logger.error('__checkImportedItemConsistency: Amount is negative.')
            return Result.INVALID_AMOUNT
        if importedItem[ImportedItemField.CHARITY] < 0 or importedItem[ImportedItemField.CHARITY] > 100:
            self.__logger.error('__checkImportedItemConsistency: Charity is not in a range [0, 100].')
            return Result.INVALID_CHARITY
        return Result.SUCCESS

    def __calculateImportItemsChecksum(self, importedItems):
        """Calculate checksum of the import.
        Returns:
            Imported item with the result inside.
        """
        checksum = 0
        for item in importedItems:
            checksum = checksum ^ calculateImportedItemChecksum(item)
        return checksum

    def __matchStrings(self, stringA, stringB):
        """Match strings, case insensitive.
        Return:
            True if string matches.
        """
        return stringA is not None and \
                    stringB is not None and \
                    str(stringA).lower() == str(stringB).lower()

    def __matchImportedItems(self, itemA, itemB):
        """Match imported items
        Returns:
            True if the items matches.
        """
        return itemA is not None and \
                itemB is not None and \
                itemA[ImportedItemField.IMPORT_RESULT] == Result.SUCCESS and \
                itemB[ImportedItemField.IMPORT_RESULT] == Result.SUCCESS and \
                self.__matchStrings(itemA[ImportedItemField.AUTHOR], itemB[ImportedItemField.AUTHOR]) and \
                self.__matchStrings(itemA[ImportedItemField.TITLE], itemB[ImportedItemField.TITLE])

    def __checkDuplicityWithinImport(self, importedItems):
        """Check whether there are duplicities within the import items."""
        for i in range(1, len(importedItems)):
            item = importedItems[i]
            if item[ImportedItemField.IMPORT_RESULT] == Result.SUCCESS:
                for j in range(0, i - 1):
                    otherItem = importedItems[j]
                    if self.__matchImportedItems(item, otherItem):
                        self.__logger.info('__checkImportedItemsDuplicity: Item {0} is duplicate of an item {1}.'.format(
                                json.dumps(otherItem, cls=JSONDecimalEncoder), json.dumps(item, cls=JSONDecimalEncoder)))
                        item[ImportedItemField.IMPORT_RESULT] = Result.DUPLICATE_ITEM
                        break

    def __postProcessImport(self, sessionID, importedItems):
        # 1. Remove previous data (if any).
        self.dropImport(sessionID)

        # 2. Calculate checksum
        importedItemsChecksum = self.__calculateImportItemsChecksum(importedItems)

        # 3. Check for duplicites
        self.__checkDuplicityWithinImport(importedItems)

        # 4. Update session.
        self.__dataset.updateSessionPairs(sessionID, **{
                session.Field.IMPORTED_ITEMS: json.dumps(importedItems),
                session.Field.IMPORTED_CHECKSUM: importedItemsChecksum})

        return importedItemsChecksum

    def isOwnerDefinedInImport(self, importedItems):
        """
        Returns:
            true if the owner is defined
        """
        ownerDefined = True
        for importedItem in importedItems:
            if importedItem[ImportedItemField.OWNER] is None \
                    or importedItem[ImportedItemField.OWNER] == '':
                ownerDefined = False
                break
        return ownerDefined

    def importCSVFile(self, sessionID, stream, headerRow=True, encoding='utf-8'):
        """Import from a CSV file.
        Args:
            sessionID -- Session ID.
            stream -- File stream.
            headerRow -- True if the first row is the header
            encoding -- Encoding of the file.
        Returns:
            imported items, checksum
        """

        # 1. Import stream.
        importedItems = []
        textReader = io.TextIOWrapper(buffer=stream, encoding=encoding, errors='replace')
        try:
            lineIndex = 0
            done = False
            csvReader = csv.reader(textReader)
            for row in csvReader:
                if not headerRow or lineIndex > 0:
                    importedItems.append(self.__procesItemImport(self.__mapCSVRowToImport(row)))
                lineIndex = lineIndex + 1
        finally:
            textReader.detach()

        # 2. Postprocess data.
        importedItemsChecksum = self.__postProcessImport(sessionID, importedItems)

        self.__logger.info('importFile: Found {0} item(s) with a checksum "{1}".'.format(
                len(importedItems), importedItemsChecksum))

        return importedItems, importedItemsChecksum

    def __mapCSVRowToImport(self, row):
        rowValueOrder = [
                ImportedItemField.NUMBER,
                ImportedItemField.OWNER,
                ImportedItemField.AUTHOR,
                ImportedItemField.TITLE,
                ImportedItemField.MEDIUM,
                ImportedItemField.NOTE,
                ImportedItemField.INITIAL_AMOUNT,
                ImportedItemField.CHARITY]
        mappedRow = {}
        i = 0
        while i < len(row) and i < len(rowValueOrder):
            mappedRow[rowValueOrder[i]] = row[i]
            i = i + 1
        return mappedRow

    def __procesItemImport(self, rawItemImport):
        """Proces item import.
        Returns:
            Imported item with the result inside.
        """
        result, item = self.__dataset.normalizeItemImport(rawItemImport)
        if result != Result.SUCCESS:
            self.__logger.error('__importRawItem: Reading a raw item "{0}" failed with a result {1}.'.format(
                    json.dumps(rawItemImport, cls=JSONDecimalEncoder), result))
        else:
            result = self.__checkImportedItemConsistency(item)
            if result != Result.SUCCESS:
                self.__logger.error('__importRawItem: Line "{0}" failed consistency check with a result {1}.'.format(
                        json.dumps(rawItemImport, cls=JSONDecimalEncoder), result))

        item[ImportedItemField.IMPORT_RESULT] = result
        return item

    def __extractTaggedValue(self, line, tags):
        """Extracts tagged value.
        Returns:
            (tag field, tag value) or (None, None) if the line does not contain a tag.
        """
        if line is None or len(line) == 0:
            return None, None

        index = 0
        while index < len(line) and not line[index].isalnum():
            index = index + 1
        line = line[index:]

        if len(line) == 0:
            return None, None

        for tag, field in tags.items():
            if line.startswith(tag):
                valueIndex = line.find(':')
                if valueIndex < 0:
                    return field, ''
                else:
                    return field, line[(valueIndex + 1):].strip(' \t\r\n')

        return None, None

    def importText(self, sessionID, text):
        """Import from text."""

        # 1. Import stream.
        firstTag = 'A)'
        tags = {
                'A)': ImportedItemField.NUMBER,
                'B)': ImportedItemField.AUTHOR,
                'C)': ImportedItemField.TITLE,
                'D)': ImportedItemField.INITIAL_AMOUNT,
                'E)': ImportedItemField.CHARITY }

        importedItems = []
        rawItem = {}
        textStream = io.StringIO(initial_value=text)
        for line in textStream:
            tagField, tagValue = self.__extractTaggedValue(line, tags)
            if tagValue is not None:            
                if tagField == tags[firstTag]:
                    if len(rawItem) != 0:
                        importedItems.append(self.__procesItemImport(rawItem))
                        rawItem.clear()
                rawItem[tagField] = tagValue

        if len(rawItem) != 0:
            importedItems.append(self.__procesItemImport(rawItem))

        # 2. Postprocess data.
        importedItemsChecksum = self.__postProcessImport(sessionID, importedItems)

        self.__logger.info('importText: Found {0} item(s) with a checksum "{1}".'.format(
                len(importedItems), importedItemsChecksum))

        return importedItems, importedItemsChecksum

    def applyImport(self, sessionID, checksum, defaultOwner):
        """Apply items from an item.
        Items which did not import well are skipped.
        Args:
            sessionID -- Session ID.
            checksum -- Import checsum.
            defaultOwner -- Owner in case owner is not defined.
        Returns:
            (result, skipped items).
        """
        # 1. Check validity of the input
        importedChecksum = self.__dataset.getSessionValue(sessionID, session.Field.IMPORTED_CHECKSUM, None)
        importedItemsRaw = self.__dataset.getSessionValue(sessionID, session.Field.IMPORTED_ITEMS)
        if importedChecksum is None or importedItemsRaw is None:
            self.__logger.debug('applyImport: There is no import to apply.')
            return Result.NO_IMPORT, []

        checksumRaw = checksum
        checksum = toInt(checksum)
        if checksum is None or importedChecksum != checksum:
            self.__logger.debug('applyImport: Checksum "{0}" does not match stored checksum "{1}".'.format(checksumRaw, importedChecksum))
            return Result.INVALID_CHECKSUM, []

        defaultOwnerRaw = defaultOwner
        defaultOwner = toInt(defaultOwner)
        if defaultOwner is not None and defaultOwner is None:
            self.__logger.error('applyImport: Default owner "{0}" is not an integer.'.format(defaultOwnerRaw))
            return Result.INPUT_ERROR, []

        importedItems = []
        try:
            importedItems = json.loads(importedItemsRaw)
        except ValueError as err:
            self.__logger.error('applyImport: Imported items [{0}] are corrupted. Decoding failed with an error {1}.'.format(
                    importedItemsRaw, str(err)))
            return Result.INPUT_ERROR, []

        # 2. Add items
        skippedItems = []
        for item in importedItems:
            if item[ImportedItemField.IMPORT_RESULT] == Result.SUCCESS:
                owner = item[ImportedItemField.OWNER] if item[ImportedItemField.OWNER] is not None else defaultOwner
                addResult = self.addNewItem(
                        sessionID,
                        owner=owner,
                        title=item[ImportedItemField.TITLE],
                        author=item[ImportedItemField.AUTHOR],
                        medium=item[ImportedItemField.MEDIUM],
                        amount=item[ImportedItemField.INITIAL_AMOUNT],
                        charity=item[ImportedItemField.CHARITY],
                        note=item[ImportedItemField.NOTE],
                        importNumber=item[ImportedItemField.NUMBER])

                if addResult == Result.DUPLICATE_IMPORT_NUMBER:
                    addResult = self.__updateImportedItem(
                        sessionID,
                        owner=owner,
                        importNumber=item[ImportedItemField.NUMBER],
                        title=item[ImportedItemField.TITLE],
                        author=item[ImportedItemField.AUTHOR],
                        medium=item[ImportedItemField.MEDIUM],
                        amount=item[ImportedItemField.INITIAL_AMOUNT],
                        charity=item[ImportedItemField.CHARITY],
                        note=item[ImportedItemField.NOTE])

                if addResult != Result.SUCCESS:
                    self.__logger.error('applyImport: Importing item {0} failed with an error {1}.'.format(
                            json.dumps(item, cls=JSONDecimalEncoder), addResult))
                    item[ImportedItemField.IMPORT_RESULT] = addResult

            if item[ImportedItemField.IMPORT_RESULT] != Result.SUCCESS:
                self.__logger.warning('applyImport: Item {0} has been skipped.'.format(
                        json.dumps(item, cls=JSONDecimalEncoder)))
                skippedItems.append(item)
            else:
                self.__logger.debug('applyImport: Item {0} has been processed.'.format(
                        json.dumps(item, cls=JSONDecimalEncoder)))

        self.__logger.info('applyImport: Added {0} item(s). Skipped {1} item(s).'.format(
                len(self.getAdded(sessionID)), len(skippedItems)))

        # 3. Drop import
        self.dropImport(sessionID)

        return Result.SUCCESS, skippedItems

    def __diffAndUpdateItem(self, itemDiff, fieldName, item, valueNew, valueRaw, required):
        """Diffs a given field of the current item and a new value and updates item.
        Raises:
            FieldValueError in a case of an error.
        """
        if valueNew is not None:
            if item[fieldName] != valueNew:
                valueOld = item[fieldName]
                item[fieldName] = valueNew
                itemDiff[fieldName] = valueNew
                self.__logger.debug(
                        '__diffAndUpdateItem: Field "{0}" will be updated from "{1}" to "{2}".'.format(
                                fieldName, valueOld, valueNew))
            else:
                self.__logger.debug('__diffAndUpdateItem: Field "{0}" not updated because it is the same.'.format(fieldName))

        elif valueRaw is None or valueRaw == '':
            if required:
                raise FieldValueError(fieldName, valueRaw)
            elif item[fieldName] is not None and item[fieldName] != '':
                item[fieldName] = None
                itemDiff[fieldName] = None

        else:
            raise FieldValueError(fieldName, valueRaw)

    def __checkDataConsistency(self, item):
        """Check logical consistency of an item.
        Returns:
            Result (class Result).
        """
        # Items which were not sold.
        if item[ItemField.STATE] in [ItemState.OPEN, ItemState.ON_SHOW]:
            # Item which does not require sale data.
            return Result.SUCCESS
        if item[ItemField.STATE] == ItemState.FINISHED:
            if item[ItemField.INITIAL_AMOUNT] is None and item[ItemField.CHARITY] is None:
                # Finished unsold or on-show item.
                return Result.SUCCESS

        # Items which might be sold.
        if item[ItemField.INITIAL_AMOUNT] is None:
            self.__logger.error('__checkItemConsistency: Item "{0}" is not consistent because initial amount is not defined.'.format(
                    item[ItemField.CODE]))
            return Result.INITIAL_AMOUNT_NOT_DEFINED
        if item[ItemField.CHARITY] is None:
            self.__logger.error('__checkItemConsistency: Item "{0}" is not consistent because charity is not defined.'.format(
                    item[ItemField.CODE]))
            return Result.CHARITY_NOT_DEFINED
        if item[ItemField.STATE] in [ItemState.ON_SALE, ItemState.NOT_SOLD]:
            # Item offered to be sold.
            return Result.SUCCESS

        # Items which were sold.
        if item[ItemField.AMOUNT] is None:
            self.__logger.error('__checkItemConsistency: Item "{0}" is not consistent because amount is not defined.'.format(
                    item[ItemField.CODE]))
            return Result.AMOUNT_NOT_DEFINED
        if item[ItemField.BUYER] is None:
            self.__logger.error('__checkItemConsistency: Item "{0}" is not consistent because buyer is not defined.'.format(
                    item[ItemField.CODE]))
            return Result.BUYER_NOT_DEFINED
        if item[ItemField.AMOUNT] < item[ItemField.INITIAL_AMOUNT]:
            self.__logger.error('__checkItemConsistency: Item "{0}" is not consistent because amount ({1}) is smaller than initial amount ({2}).'.format(
                    item[ItemField.CODE], item[ItemField.AMOUNT], item[ItemField.INITIAL_AMOUNT]))
            return Result.AMOUNT_TOO_LOW

        return Result.SUCCESS

    def __updateImportedItem(self, sessionID, owner, importNumber, title, author, medium, amount, charity, note):
        """Update item based on the pair (owner, importNumber).
        Returns:
            Result code (class Result).
        """
        item = self.__getImportedItem(owner, importNumber)
        if item is None:
            self.__logger.error(
                    'updateImportedItem: Import number "{0}" of owner "{1}" not fount.'.format(
                    importNumber, owner))
            return Result.ITEM_NOT_FOUND

        if item[ItemField.STATE] in ItemState.AMOUNT_SENSITIVE:
            self.__logger.error(
                    'updateImportedItem: Import number "{0}" of owner "{1}" is already closed.'.format(
                    importNumber, owner))
            return Result.ITEM_CLOSED_ALREADY

        updateResult = self.updateItem(
                itemCode=item[ItemField.CODE],
                owner=item[ItemField.OWNER],
                title=title,
                author=author,
                medium=medium,
                initialAmount=amount,
                charity=charity,
                note=note,
                state=self.__evaluateState(amount, charity),
                amount=item[ItemField.AMOUNT],
                buyer=item[ItemField.BUYER])

        if updateResult == Result.SUCCESS:
            addedItemCodes = self.__appendAddedCode(sessionID, item[ItemField.CODE])
            self.__logger.info('__updateImportedItem: Updated item "{0}" (added codes: {1})'.format(item[ItemField.CODE], addedItemCodes))

        return updateResult

    def updateItem(self, itemCode, owner, title, author, medium, state, initialAmount, charity, amount, buyer, note):
        # 1. Get the original item.
        item = self.getItem(itemCode)
        if item is None:
            self.__logger.error('updateItem: Item "{0}" not fount'.format(itemCode))
            return Result.ITEM_NOT_FOUND

        # 2. Build list of compoments to be updated and check value ranges.
        itemDiff = {}
        try:
            self.__diffAndUpdateItem(
                    itemDiff, ItemField.OWNER, item, 
                    checkRange(toInt(owner), 1, None), owner, True)
            self.__diffAndUpdateItem(
                    itemDiff, ItemField.TITLE, item,
                    title, title, False)
            self.__diffAndUpdateItem(
                    itemDiff, ItemField.AUTHOR, item,
                    author, author, False)
            self.__diffAndUpdateItem(
                    itemDiff, ItemField.MEDIUM, item,
                    medium, medium, False)
            self.__diffAndUpdateItem(
                    itemDiff, ItemField.STATE, item,
                    state, state, True)
            self.__diffAndUpdateItem(
                    itemDiff, ItemField.INITIAL_AMOUNT, item,
                    checkRange(toDecimal(initialAmount), 1, None), initialAmount, False)
            self.__diffAndUpdateItem(
                    itemDiff, ItemField.CHARITY, item,
                    checkRange(toDecimal(charity), 0, 100), charity, False)
            self.__diffAndUpdateItem(
                    itemDiff, ItemField.AMOUNT, item,
                    checkRange(toDecimal(amount), 1, None), amount, False)
            self.__diffAndUpdateItem(
                    itemDiff, ItemField.BUYER, item,
                    checkRange(toInt(buyer), 1, None), buyer, False)
            self.__diffAndUpdateItem(
                    itemDiff, ItemField.NOTE, item,
                    note, note, False)
        except FieldValueError as error:
            self.__logger.error('updateItem: Update of an item "{0}" failed due to a value "{1}" of a field {2}'.format(
                    itemCode, error.rawValue, error.name))
            return Result.INVALID_VALUE

        # 3. Check consistency of the result.
        consistencyResult = self.__checkDataConsistency(item)
        if consistencyResult != Result.SUCCESS:
            self.__logger.info('updateItem: Item "{0}" not updated because it is not consistent (consistency result: {1})'.format(itemCode, consistencyResult))
            return consistencyResult

        # 4. Perform an update.
        if len(itemDiff) == 0:
            self.__logger.info('updateItem: Item "{0}" not updated because there is nothing to update'.format(itemCode))
            return Result.NOTHING_TO_UPDATE
        elif self.__dataset.updateItem(itemCode, **itemDiff):
            self.__logger.info('updateItem: Item "{0}" has been updated.'.format(itemCode))
            return Result.SUCCESS
        else:
            self.__logger.error('updateItem: Updating an item "{0}" has failed.'.format(itemCode))
            return Result.ERROR;
                
    def __updateSortCode(self, items):
        """Convert code of an item to an integer for each item."""
        if items is not None and len(items) > 0:
            for item in items:
                sortCode = 0
                code = item.get(ItemField.CODE, '0')
                if len(code) > 0:
                    if code[0].isalpha():
                        sortCode = (ord(code[0]) * 10000) + int(code[1:])
                    else:
                        sortCode = int(code)
                item[ItemField.SORT_CODE] = sortCode
        return items

    def __updatePermissions(self, items):
        """Updare permissions for each item."""
        if items is not None and len(items) > 0:
            for item in items: 
                printDeleteAllowed = item[ItemField.STATE] in [
                        ItemState.OPEN, ItemState.ON_SHOW, ItemState.ON_SALE]
                item[ItemField.PRINT_ALLOWED] = printDeleteAllowed
                item[ItemField.DELETE_ALLOWED] = printDeleteAllowed
        return items

    def __updateNetAmount(self, items):
        """Update items with net amout and net charity amount for each item."""
        if items is not None and len(items) > 0:
            for item in items:
                if item[ItemField.AMOUNT] is not None:
                    item[ItemField.NET_AMOUNT], item[ItemField.NET_CHARITY_AMOUNT] = self.getItemNetAmount(item)
                else:                    
                    item[ItemField.NET_AMOUNT] = None
                    item[ItemField.NET_CHARITY_AMOUNT] = None
        return items

    def __updateItemAmountCurrency(self, items):
        """Update items with currency specific amount for each item."""
        self.__currency.updateAmountWithAllCurrencies(
                items, {
                        ItemField.INITIAL_AMOUNT: ItemField.INITIAL_AMOUNT_IN_CURRENCY,
                        ItemField.AMOUNT: ItemField.AMOUNT_IN_CURRENCY,
                        ItemField.AMOUNT_IN_AUCTION: ItemField.AMOUNT_IN_AUCTION_IN_CURRENCY })
        return items

    def getAllItems(self):
        return self.__updatePermissions(
                self.__updateSortCode(
                        self.__dataset.getItems(None)))
        
    def getAllClosableItems(self):
        return self.__updateSortCode(
                self.__dataset.getItems('State == "{0}"'.format(
                        ItemState.ON_SALE)))

    def getAllItemsInAuction(self):
        return self.__updateSortCode(
                self.__dataset.getItems('State == "{0}"'.format(
                        ItemState.IN_AUCTION)))

    def getAllPontentiallySoldItems(self):
        rawItems = self.__updateSortCode(
                self.__dataset.getItems('State in [{0}]'.format(toQuotedStr(
                        [ItemState.IN_AUCTION, ItemState.SOLD, ItemState.DELIVERED, ItemState.FINISHED]))))

        # Filter item which have zero amount
        items = []
        for item in rawItems:
            if (item[ItemField.AMOUNT] or 0) > 0 and (item[ItemField.CHARITY] or 0) >= 0:
                items.append(item)
                
        self.__logger.info('getAllPontentiallySoldItems: Retrieved {0} potentially sold items.'.format(len(items)))
                
        return items

    def isItemClosable(self, item):
        return (item is not None) and (ItemField.STATE in item) and (item[ItemField.STATE] == ItemState.ON_SALE)
        
    def isItemDeliverable(self, item):
        return (item is not None) and (ItemField.STATE in item) and (item[ItemField.STATE] in [ItemState.SOLD, ItemState.NOT_SOLD, ItemState.ON_SHOW])
    
    def getNetAmount(self, grossAmount, charityPercent):
        """Calculate a net amount out of a gross amount.
        Args:
            grossAmount: Gross amount.
            charityPercent: 1 = 1%
        Returns:
            A tuple (net sale amount, net charity amount)"""
        try:        
            if grossAmount is None or charityPercent is None:
                self.__logger.error('getItem: Invalid input parameters. Returning zeros.')
                return (Decimal(0), Decimal(0))
            else:
                grossCharity = charityPercent / Decimal(100)

                charityAmount = self.__currency.roundInPrimary(grossAmount * grossCharity)
                netSaleAmount = grossAmount - charityAmount
                return (netSaleAmount, charityAmount)
        except decimal.InvalidOperation:
            self.__logger.exception('getItem: Invalid operation occurred for amount "{0}" and charity "{1}". Returning zeros.'.format(\
                    str(grossAmount), str(grossCharity)))
            return (Decimal(0), Decimal(0))


    def getItemNetAmount(self, item):
        """Calulates the final net amount out of an item.
        Args:
            item: An item.
        Returns:
            A tuple (net sold amount, net charity amount)"""
        ZERO = (Decimal(0), Decimal(0))
        if item is None:
            return ZERO
        elif item[ItemField.STATE] not in [ItemState.IN_AUCTION, ItemState.SOLD, ItemState.DELIVERED, ItemState.FINISHED]:
            return ZERO
        elif ItemField.AMOUNT not in item or ItemField.CHARITY not in item:
            return ZERO
        else:
            return self.getNetAmount(item[ItemField.AMOUNT], item[ItemField.CHARITY])

    def getItemPotentialNetAmount(self, item):
        """Calculates a potential net amount out of an item.
        Args:
            item: An item.
        Returns:
            A tuple (net sold amount, net charity amount)"""
        ZERO = (Decimal(0), Decimal(0))
        if item is None:
            return ZERO
        elif item[ItemField.STATE] not in [ItemState.IN_AUCTION, ItemState.SOLD, ItemState.DELIVERED, ItemState.FINISHED]:
            return ZERO
        elif ItemField.AMOUNT not in item or ItemField.CHARITY not in item:
            return ZERO
        elif item[ItemField.STATE] == ItemState.IN_AUCTION:
            return self.getNetAmount(
                    item[ItemField.AMOUNT_IN_AUCTION] or item[ItemField.AMOUNT] or Decimal(0),
                    item[ItemField.CHARITY] or 0)
        else:
            return self.getNetAmount(item[ItemField.AMOUNT] or Decimal(0), item[ItemField.CHARITY] or 0)

    def getItems(self, itemCodes):
        if len(itemCodes) > 0:
            return self.__updateItemAmountCurrency(
                    self.__updateSortCode(
                            self.__dataset.getItems(
                                    'Code in [{0}]'.format(toQuotedStr(itemCodes)))))
        else:
            return []
     
    def getItem(self, itemCode):
        if itemCode is None:
            self.__logger.error('getItem: Item code not specified.')
            return None
        else:
            items = self.getItems([itemCode])
            if len(items) > 0:
                return items[0]
            else:
                self.__logger.info('getItem: Item "{0}" not found.'.format(itemCode))
                return None

    def deleteItems(self, itemCodes):
        """Delete item codes.
        Returns:
            Number of deleted items.
        """
        return self.__dataset.items().delete('Code in [{0}]'.format(toQuotedStr(itemCodes)))

    def __validateSaleInput(self, itemCode, item, amount, buyer):
        amount = toDecimal(amount)
        buyer = toInt(buyer)

        if itemCode == None:
            self.__logger.error('__validateSaleInput: Invalid item code.')
            return Result.INVALID_ITEM_CODE            
        if item is None:
            self.__logger.error('__validateSaleInput: Item "{0}" not found.'.format(itemCode))
            return Result.ITEM_NOT_FOUND
        elif not self.isItemClosable(item):
            self.__logger.error('__validateSaleInput: Item "{0}" is not closable.'.format(itemCode))
            return Result.ITEM_NOT_CLOSABLE
        elif buyer is None or buyer <= 0:
            self.__logger.error('__validateSaleInput: Buyer not provided or invalid for item "{0}".'.format(itemCode))
            return Result.INVALID_BUYER
        elif amount is None:
            self.__logger.error('__validateSaleInput: Amount not provided or invalid for item "{0}".'.format(itemCode))
            return Result.INVALID_AMOUNT
        elif amount < item[ItemField.INITIAL_AMOUNT]:
            self.__logger.error(
                    '__validateSaleInput: Amount {0} is too low an item "{1}"'.format(
                            itemCode, amount))
            return Result.AMOUNT_TOO_LOW
        else:
            return Result.SUCCESS
        
    def closeItemAsNotSold(self, itemCode):
        """Close item as sold.
        Returns:
            Result (class Result).
        """
        item = self.getItem(itemCode)
        if item == None:
            self.__logger.error('closeItemAsNotSold: Item "{0}" not found.'.format(itemCode))
            return Result.ITEM_NOT_FOUND
        elif not self.isItemClosable(item):
            self.__logger.error('closeItemAsNotSold: Item "{0}" is not closable.'.format(itemCode))
            return Result.ITEM_NOT_CLOSABLE
        else:
            numUpdated = self.__dataset.updateItem(
                    itemCode,
                    **{
                            ItemField.STATE: ItemState.NOT_SOLD,
                            ItemField.AMOUNT: None,
                            ItemField.BUYER: None})
            if numUpdated != 1:
                self.__logger.error('closeItemAsNotSold: Item "{0}" did not update.'.format(itemCode))
                return Result.ERROR
            else:
                self.__logger.info('closeItemAsNotSold: Item "{0}" set as not sold.'.format(itemCode))
                return Result.SUCCESS
                
    def closeItemAsSold(self, itemCode, amount, buyer):
        item = self.getItem(itemCode)

        result = self.__validateSaleInput(itemCode, item, amount, buyer)
        if result != Result.SUCCESS:
            self.__logger.error(
                    'closeItemAsSold: Closing item "{0}" (amount: {1}, buyer: {2}) failed.'.format(
                            itemCode, buyer, amount))
            return result
        else:
            numUpdated = self.__dataset.updateItem(
                    itemCode,
                    **{
                            ItemField.STATE: ItemState.SOLD,
                            ItemField.AMOUNT: toDecimal(amount),
                            ItemField.BUYER: toInt(buyer)})
            if numUpdated != 1:
                self.__logger.error('closeItemAsSold: Item "{0}" did not update.'.format(itemCode))
                return Result.ERROR
            else:
                self.__logger.info(
                        'closeItemAsSold: Item "{0}" set as sold to {1} for {2}.'.format(
                            itemCode, buyer, amount))
                return Result.SUCCESS
        
    def closeItemIntoAuction(self, itemCode, amount, buyer):
        item = self.getItem(itemCode)

        result = self.__validateSaleInput(itemCode, item, amount, buyer)
        if result != Result.SUCCESS:
            self.__logger.error('closeItemIntoAuction: Closing item %(code)s (amount: %(amount)s, buyer: %(buyer)s) failed.'
                % { 'code': itemCode, 'buyer': buyer, 'amount': amount })
            return result
        else:
            numUpdated = self.__dataset.updateItem(
                    itemCode,
                    **{
                            ItemField.STATE: ItemState.IN_AUCTION,
                            ItemField.AMOUNT: toDecimal(amount),
                            ItemField.BUYER: toInt(buyer)})
            if numUpdated != 1:
                self.__logger.error('closeItemIntoAuction: Item ''%(code)s'' did not update.' % { 'code': itemCode })
                return Result.ERROR
            else:
                self.__logger.info('closeItemIntoAuction: Item ''%(code)s'' moved to auction with amount %(amount)s (the last buyer %(buyer)s).'
                    % { 'code': itemCode, 'buyer': buyer, 'amount': amount })
                return Result.SUCCESS

    def __convertAmountToCurrencies(self, amount, currencyInfoList):
        """ Convert amount to given currencies.
        Args:
            amount(Decimal)
            currencyInfoList(list of dict[CurrencyField])
        Returns:
            Array of amount in various currencies including formatting info (CurrencyField).
            Primary currency is at index 0.
        """
        if amount is None:
            return []

        currencyInfoList = [currencyInfo.copy() for currencyInfo in currencyInfoList]
        for currencyInfo in currencyInfoList:
            if currencyInfo[CurrencyField.AMOUNT_IN_PRIMARY] > 0:
                try:
                    oneInFixedPoint = Decimal(10) ** currencyInfo[CurrencyField.DECIMAL_PLACES]
                    convertedAmountFixedPoint = (amount * oneInFixedPoint) / currencyInfo[CurrencyField.AMOUNT_IN_PRIMARY];
                    currencyInfo[CurrencyField.AMOUNT] = convertedAmountFixedPoint.quantize(1, rounding=decimal.ROUND_HALF_UP) / oneInFixedPoint
                except decimal.InvalidOperation:
                    self.__logger.exception(
                            '__convertAmountToCurrencies: Amount "{0}" and currency "{1}" caused invalid opreration. Returning zeros.'.format(
                                        str(amount), str(currencyInfo[CurrencyField.CODE])))
                    currencyInfo[CurrencyField.AMOUNT] = Decimal(0)
            else:
                currencyInfo[CurrencyField.AMOUNT] = Decimal(0)
        return currencyInfoList

    def getCurrency(self):
        """ Get currency setup.
        Returns:
            Instance of the active class Currency.
        """
        return self.__currency
     
    def getPotentialCharityAmount(self):
        soldItems = self.getAllPontentiallySoldItems()
        totalCharityAmount = Decimal(0)
        for item in soldItems:
            netAmount, netCharityAmount = self.getItemPotentialNetAmount(item)
            totalCharityAmount = totalCharityAmount + netCharityAmount
        return totalCharityAmount
        
    def getItemInAuction(self):
        itemInAuction = self.__dataset.getItem(self.__dataset.getGlobalValue('ItemCodeInAuction'))
        if itemInAuction is not None and itemInAuction[ItemField.STATE] != ItemState.IN_AUCTION:
            self.__logger.error('getItemInAuction: Item "{0}" is not in auction'.format(itemInAuction[ItemField.CODE]))
            return None
        elif itemInAuction is None:
            return None
        else:
            return self.__updateItemAmountCurrency([itemInAuction])[0]

    def sendItemToAuction(self, itemCode):
        item = self.__dataset.getItem(itemCode)
        if item is None:
            self.__logger.error('sendItemInAuction: Item "{0}" has not been found'.format(itemCode))
            itemToAuction = None
        elif item[ItemField.STATE] != ItemState.IN_AUCTION:
            self.__logger.error('sendItemInAuction: Item "{0}" has incompatible state {1}'.format(itemCode, item[ItemField.STATE]))
            itemToAuction = None
        else:            
            item[ItemField.AMOUNT_IN_AUCTION] = item[ItemField.AMOUNT]
            if not self.__dataset.updateItem(item[ItemField.CODE], **item):
                self.__logger.error('sendItemInAuction: Item "{0}" had not been updated'.format(itemCode))
                itemToAuction = None
            else:
                itemToAuction = item

        if itemToAuction is None:
            self.__dataset.updateGlobalPairs(ItemCodeInAuction=None)
        else:
            self.__dataset.updateGlobalPairs(ItemCodeInAuction=itemCode)

        return itemToAuction

    def updateItemInAuction(self, newAmount):
        item = self.getItemInAuction()
        if item is None:
            self.__logger.error('updateAmountItemInAuction: No valid item in auction')
            return False
        else:
            item[ItemField.AMOUNT_IN_AUCTION] = toDecimal(newAmount)
            if not self.__dataset.updateItem(item[ItemField.CODE], **item):
                self.__logger.error('updateAmountItemInAuction: Item "{0}" had not been updated'.format(item[ItemField.CODE]))
                return False
            else:
                return True
    
    def sellItemInAuction(self, newBuyer):
        newBuyerInt = toInt(newBuyer)
        if newBuyerInt is None:
            self.__logger.error('sellItemInAuction: Buyer "{0}" is not a valid buyer '.format(newBuyer or '<None>'))
            return False
        else:
            item = self.getItemInAuction()
            if item is None:
                self.__logger.error('sellItemInAuction: No valid item in auction')
                return False
            else:
                item[ItemField.STATE] = ItemState.SOLD
                item[ItemField.BUYER] = newBuyer
                item[ItemField.AMOUNT] = item[ItemField.AMOUNT_IN_AUCTION]
                item[ItemField.AMOUNT_IN_AUCTION] = None
                if not self.__dataset.updateItem(item[ItemField.CODE], **item):
                    self.__logger.error('sellItemInAuction: Item "{0}" had not been updated'.format(item[ItemField.CODE]))
                    return False
                else:
                    self.__logger.info('sellItemInAuction: Item "{0}" had been sold to buyer {1} for {2}'.format(item[ItemField.CODE], item[ItemField.BUYER], item[ItemField.AMOUNT]))
                    self.__dataset.updateGlobalPairs(ItemCodeInAuction=None)
                    return True
        
    def sellItemInAuctionNoChange(self):
        item = self.getItemInAuction()
        if item is None:
            self.__logger.error('sellItemInAuctionNoChange: No valid item in auction')
            return False
        else:
            item[ItemField.STATE] = ItemState.SOLD
            item[ItemField.AMOUNT_IN_AUCTION] = None
            if not self.__dataset.updateItem(item[ItemField.CODE], **item):
                self.__logger.error('sellItemInAuctionNoChange: Item "{0}" had not been updated'.format(item[ItemField.CODE]))
                return False
            else:
                self.__logger.info('sellItemInAuctionNoChange: Item "{0}" had been sold to buyer {1} for {2}'.format(item[ItemField.CODE], item[ItemField.BUYER], item[ItemField.AMOUNT]))
                self.__dataset.updateGlobalPairs(ItemCodeInAuction=None)
                return True

    def clearAuction(self):
        item = self.getItemInAuction()
        if item is not None:
            item[ItemField.AMOUNT_IN_AUCTION] = None
            self.__dataset.updateItem(item[ItemField.CODE], **item)
            self.__logger.debug('clearAuction: Item "{0}" has been removed from auction'.format(item[ItemField.CODE]))

        self.__dataset.updateGlobalPairs(ItemCodeInAuction=None)

    def getBadgeReconciliationSummary(self, badge):
        badgeNum = toInt(badge)
        if badgeNum is None:
            self.__logger.error('getBadgeReconciliationSummary: Badge "{0}" is invalid'.format(badge))
            return None
        else:
            availableUnsoldItems = self.__updateSortCode(self.__dataset.getItems(
                    'Owner == "{0}" and State in [{1}]'.format(
                        badgeNum, toQuotedStr([ItemState.ON_SHOW, ItemState.NOT_SOLD]))))

            availableBoughtItems = self.__updateSortCode(self.__dataset.getItems(
                    'Buyer == "{0}" and State == "{1}"'.format(
                        badge, ItemState.SOLD)))
            boughtItemsAmount = Decimal(0)
            for item in availableBoughtItems:
                boughtItemsAmount = boughtItemsAmount + item[ItemField.AMOUNT]

            deliveredSoldItems = self.__updateNetAmount(self.__updateSortCode(self.__dataset.getItems(
                    'Owner == "{0}" and State == "{1}"'.format(
                        badge, ItemState.DELIVERED))))
            charityDeduction = Decimal(0)
            netSaleAmount = Decimal(0)
            for item in deliveredSoldItems:
                itemNetSaleAmount, itemCharityAmount = self.getItemNetAmount(item)
                netSaleAmount = netSaleAmount + itemNetSaleAmount
                charityDeduction = charityDeduction + itemCharityAmount

            pendingSoldItems = self.__updateNetAmount(self.__updateSortCode(self.__dataset.getItems(
                    'Owner == "{0}" and State == "{1}"'.format(
                        badge, ItemState.SOLD))))

            return {
                    SummaryField.AVAILABLE_UNSOLD_ITEMS: availableUnsoldItems,
                    SummaryField.AVAILABLE_BOUGHT_ITEMS: availableBoughtItems,
                    SummaryField.DELIVERED_SOLD_ITEMS: deliveredSoldItems,
                    SummaryField.PENDING_SOLD_ITEMS: pendingSoldItems,
                    SummaryField.GROSS_SALE_AMOUNT: netSaleAmount + charityDeduction,
                    SummaryField.CHARITY_DEDUCTION: charityDeduction,
                    SummaryField.BOUGHT_ITEMS_AMOUNT: boughtItemsAmount,
                    SummaryField.TOTAL_DUE_AMOUNT: boughtItemsAmount - netSaleAmount}

    def reconciliateBadge(self, badge):
        badgeNum = toInt(badge)
        if badgeNum is None:
            self.__logger.error('reconciliateBadge: Badge "{0}" is invalid'.format(badge))
            return False
        else:
            # delivered items first
            self.__dataset.updateMultipleItems(
                    'Owner == "{0}" and State == "{1}"'.format(
                        badge, ItemState.DELIVERED),
                    **{ItemField.STATE: ItemState.FINISHED})

            # bought items second
            self.__dataset.updateMultipleItems(
                    'Buyer == "{0}" and State == "{1}"'.format(
                        badge, ItemState.SOLD),
                    **{ItemField.STATE: ItemState.DELIVERED})

            # unsold items third
            self.__dataset.updateMultipleItems(
                    'Owner == "{0}" and State in [{1}]'.format(
                        badgeNum, toQuotedStr([ItemState.ON_SHOW, ItemState.NOT_SOLD])),
                    **{ItemField.STATE: ItemState.FINISHED})

            return True

    def __getAddActorSummary(self, badge, dict):
        if badge not in dict:
            dict[badge] = ActorSummary(badge)
        return dict[badge]

    def getCashDrawerSummary(self):
        items = self.__dataset.getItems(None)

        totalGrossCashDrawerAmount = 0
        totalNetCharityAmount = 0
        buyersToBeCleared = {}
        ownersToBeCleared = {}
        pendingItems = []
        for item in items:
            if item[ItemField.STATE] == ItemState.FINISHED:
                netSaleAmount, netCharityAmount = self.getItemNetAmount(item)
                totalNetCharityAmount = totalNetCharityAmount + netCharityAmount
                totalGrossCashDrawerAmount = totalGrossCashDrawerAmount + netCharityAmount

            elif item[ItemField.STATE] == ItemState.DELIVERED:
                netSaleAmount, netCharityAmount = self.getItemNetAmount(item)
                totalNetCharityAmount = totalNetCharityAmount + netCharityAmount
                totalGrossCashDrawerAmount = totalGrossCashDrawerAmount + netSaleAmount + netCharityAmount
                self.__getAddActorSummary(item[ItemField.OWNER], ownersToBeCleared).addItemToFinish(netSaleAmount)

            elif item[ItemField.STATE] == ItemState.SOLD:
                self.__getAddActorSummary(item[ItemField.BUYER], buyersToBeCleared).addItemToReceive(item[ItemField.AMOUNT])

            elif item[ItemField.STATE] in [ItemState.ON_SHOW, ItemState.NOT_SOLD]:
                self.__getAddActorSummary(item[ItemField.OWNER], ownersToBeCleared).addItemToFinish(0)

            else:
                pendingItems.append(item)

        return {
                DrawerSummaryField.TOTAL_GROSS_CASH_DRAWER_AMOUNT: totalGrossCashDrawerAmount,
                DrawerSummaryField.TOTAL_NET_CHARITY_AMOUNT: totalNetCharityAmount,
                DrawerSummaryField.TOTAL_NET_AVAILABLE_AMOUNT: totalGrossCashDrawerAmount - totalNetCharityAmount,
                DrawerSummaryField.BUYERS_TO_BE_CLEARED: list(buyersToBeCleared.values()),
                DrawerSummaryField.OWNERS_TO_BE_CLEARED: list(ownersToBeCleared.values()),
                DrawerSummaryField.PENDING_ITEMS: self.__updateSortCode(pendingItems)}