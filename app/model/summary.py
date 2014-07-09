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
class SummaryField:
    AVAILABLE_UNSOLD_ITEMS = 'AvailUnsoldItems'
    AVAILABLE_BOUGHT_ITEMS = 'AvailBoughtItems'
    DELIVERED_SOLD_ITEMS = 'DeliveredSoldItems'
    PENDING_SOLD_ITEMS = 'PendingSoldItems'

    GROSS_SALE_AMOUNT = 'GrossSaleAmount'
    CHARITY_DEDUCTION = 'CharityDeduction'
    BOUGHT_ITEMS_AMOUNT = 'BoughtItemsAmount'
    TOTAL_DUE_AMOUNT = 'TotalDueAmount'

class DrawerSummaryField:
    TOTAL_GROSS_CASH_DRAWER_AMOUNT = 'TotalGrossCashDrawerAmount'
    TOTAL_NET_CHARITY_AMOUNT = 'TotalNetCharityAmount'
    TOTAL_NET_AVAILABLE_AMOUNT = 'TotalNetAvailableAmount'
    BUYERS_TO_BE_CLEARED = 'BuyersToBeCleared'
    OWNERS_TO_BE_CLEARED = 'OwnersToBeCreared'
    PENDING_ITEMS = 'PendingItems'

class ActorSummary:
    def __init__(self, badge):
        self.Badge = badge

        self.ItemsToRetrieve = 0
        self.AmountToPay = 0

        self.ItemsToFinish = 0
        self.AmountToReceive = 0

    def addItemToReceive(self, grossAmount):
        """Add an gross amount of an item which this actor should receive
        because the actor is a buyer."""
        self.ItemsToRetrieve = self.ItemsToRetrieve + 1
        self.AmountToPay = self.AmountToPay + (grossAmount or 0)

    def addItemToFinish(self, netAmount):
        """Add a net amount of an item which this actor should receive
        because the actor is a former owner."""
        self.ItemsToFinish = self.ItemsToFinish + 1
        self.AmountToReceive = self.AmountToReceive + (netAmount or 0)

class Summary:
    def calculateChecksum(summary):
        """Calculate checksum which is reasonably unique.
        Args:
            summary: Summary dictionary."""
        if summary is None:
            return 0
        else:
            checksum = 0
            checksum = (checksum * 15) ^ len(summary[SummaryField.PENDING_SOLD_ITEMS])
            checksum = (checksum * 13) ^ len(summary[SummaryField.AVAILABLE_UNSOLD_ITEMS])
            checksum = (checksum * 11) ^ len(summary[SummaryField.AVAILABLE_BOUGHT_ITEMS])
            checksum = (checksum * 7) ^ len(summary[SummaryField.DELIVERED_SOLD_ITEMS])
            checksum = (checksum * 5) ^ int((summary[SummaryField.GROSS_SALE_AMOUNT] * 1000).quantize(0))
            checksum = (checksum * 3) ^ int((summary[SummaryField.BOUGHT_ITEMS_AMOUNT] * 1000).quantize(0))
            return checksum
