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

class ItemState:
    OPEN = 'OPEN' # Next: OPEN, ON_SALE
    ON_SHOW = 'SHOW' # Next: FINISHED
    ON_SALE = 'ONSL' # Next: IN_AUCTION, SOLD, NOT_SOLD
    IN_AUCTION = 'AUCT' # Next: SOLD
    SOLD = 'SOLD' # Next: DELIVERED
    NOT_SOLD = 'NSOL' # Next: FINISHED
    DELIVERED = 'DLVR' # Next: FINISHED
    FINISHED = 'FINI' # Finish

    ALL = sorted([OPEN, ON_SHOW, ON_SALE, IN_AUCTION, SOLD, NOT_SOLD, DELIVERED, FINISHED])
    AMOUNT_SENSITIVE = sorted([IN_AUCTION, SOLD, NOT_SOLD, DELIVERED, FINISHED])

class ItemField:
    CODE = 'Code'
    OWNER = 'Owner'
    TITLE = 'Title'
    AUTHOR = 'Author'
    MEDIUM = 'Medium'
    NOTE = 'Note'
    STATE = 'State'
    CHARITY = 'Charity'    
    INITIAL_AMOUNT = 'InitialAmount'
    BUYER = 'Buyer'
    AMOUNT = 'Amount'
    IMPORT_NUMBER = 'ImportNumber'

    AMOUNT_IN_AUCTION = 'AmountInAuction'

    FOR_SALE = 'ForSale'
    SORT_CODE = 'SortCode'
    NET_AMOUNT = 'NetAmount'
    NET_CHARITY_AMOUNT = 'NetCharityAmount'
    PRINT_ALLOWED = 'PrintAllowed'
    DELETE_ALLOWED = 'DeleteAllowed'

    INITIAL_AMOUNT_IN_CURRENCY = 'InitialAmountInCurrency'
    AMOUNT_IN_CURRENCY = 'AmountInCurrency'
    AMOUNT_IN_AUCTION_IN_CURRENCY = 'AmountInAuctionInCurrency'

    FORMATTED = 'Formatted'

    ALL_PERSISTENT = sorted([CODE, STATE, OWNER, AUTHOR, TITLE, MEDIUM, NOTE, IMPORT_NUMBER, CHARITY, INITIAL_AMOUNT, BUYER, AMOUNT, AMOUNT_IN_AUCTION])
        
class ImportedItemField:
    NUMBER = 'NMBR'
    OWNER = 'OWNR'
    AUTHOR = 'AUTH'
    TITLE = 'TITL'
    MEDIUM = 'MEDM'
    NOTE = 'NOTE'
    INITIAL_AMOUNT = 'IAMT'
    CHARITY = 'CHAR'
    IMPORT_RESULT = 'IRES'

def __calculateComponentChecksum(value):
    checksum = 0
    if value is not None:
        string = str(value)
        for ch in string:
            checksum = checksum ^ ord(ch)
    return checksum

def calculateImportedItemChecksum(importedItem):
    """Calculate checksum of an imported item.
    Returns:
        Checksum
    """
    checksum = __calculateComponentChecksum(importedItem.get(ImportedItemField.IMPORT_RESULT, None))
    checksum = (checksum * 3) ^ __calculateComponentChecksum(importedItem[ImportedItemField.AUTHOR])
    checksum = (checksum * 3) ^ __calculateComponentChecksum(importedItem[ImportedItemField.TITLE])
    checksum = (checksum * 3) ^ __calculateComponentChecksum(importedItem[ImportedItemField.INITIAL_AMOUNT])
    checksum = (checksum * 3) ^ __calculateComponentChecksum(importedItem[ImportedItemField.CHARITY])

    return checksum
