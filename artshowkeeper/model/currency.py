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
import decimal

from . currency_field import CurrencyField
from . dataset import Dataset
from artshowkeeper.common.convert import *

class Currency:
    def __init__(self, logger, dataset, currencyCodes):
        self.__logger = logger
        self.__dataset = dataset
        self.__currencyCodes = currencyCodes
        self.__amountDecimalPlaces = self.__dataset.getCurrencyInfo(self.__currencyCodes)[0][CurrencyField.DECIMAL_PLACES]

    def getDecimalPlaces(self):
        """Valid decimal places in primary currency."""
        return self.__amountDecimalPlaces

    def getInfo(self):
        """ Get currency info.
        Returns:
            List of dict(CurrencyField)
        """
        return self.__dataset.getCurrencyInfo(self.__currencyCodes)

    def updateInfo(self, currencyInfoList):
        """ Update currency info with amount in primary.
        Args:
            currencyInfoList(list of dict(CurrencyField))
        Returns:
            Result
        """
        if currencyInfoList is not None and len(currencyInfoList) > 0:
            primaryAmountInPrimary = toDecimal(currencyInfoList[0].get(CurrencyField.AMOUNT_IN_PRIMARY, None))
            if primaryAmountInPrimary is not None and primaryAmountInPrimary != Decimal(1):
                return Result.PRIMARY_AMOUNT_IN_PRIMARY_INVALID

        return self.__dataset.updateCurrencyInfo(currencyInfoList)


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


    def __updateAmountWithCurrency(self, element, fields, currencyInfoList):
        for sourceKey, targetKey in fields.items():
            amount = element.get(sourceKey, None)
            element[targetKey] = self.__convertAmountToCurrencies(amount, currencyInfoList)


    def updateAmountWithAllCurrencies(self, entity, fields):
        if entity is None:
            return

        currencyInfoList = self.getInfo()
        if isinstance(entity, list):
            for element in entity:
                self.__updateAmountWithCurrency(element, fields, currencyInfoList)
        else:
            self.__updateAmountWithCurrency(entity, fields, currencyInfoList)

                
    def convertToAllCurrencies(self, amount):
        return self.__convertAmountToCurrencies(
                amount,
                self.getInfo())


    def roundInPrimary(self, value):
        value = toDecimal(value)
        if value is not None:
            value = value.quantize(
                    Decimal(10) ** -self.__amountDecimalPlaces,
                    rounding=decimal.ROUND_HALF_UP)
        return value
