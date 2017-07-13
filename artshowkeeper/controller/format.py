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
from artshowkeeper.common.convert import *
from artshowkeeper.model.item import ItemField
from artshowkeeper.model.currency import CurrencyField

class LangaugeField:
    THOUSANDS_SEPARATOR = 'ThousandsSeparator'
    DECIMAL_DOT = 'DecimalDot'

__LANGUAGES = {
        'cz': {
                LangaugeField.THOUSANDS_SEPARATOR: ' ',
                LangaugeField.DECIMAL_DOT: ','},
        'en': {
                LangaugeField.THOUSANDS_SEPARATOR: ',',
                LangaugeField.DECIMAL_DOT: '.'},
        'de': {
                LangaugeField.THOUSANDS_SEPARATOR: '.',
                LangaugeField.DECIMAL_DOT: ','},
        None: {
                LangaugeField.THOUSANDS_SEPARATOR: '',
                LangaugeField.DECIMAL_DOT: '.'}}

def formatNumber(number, decimalPlaces, language):
    if toDecimal(number) is None:
        return '0'
    else:
        if language not in __LANGUAGES:
            language = None
        languageInfo = __LANGUAGES[language]

        numberFormat = "{:,.0" + str(decimalPlaces or 0) + "f}"
        return numberFormat.format(toDecimal(number)). \
                    replace('.', '|'). \
                        replace(',', languageInfo[LangaugeField.THOUSANDS_SEPARATOR]). \
                            replace('|', languageInfo[LangaugeField.DECIMAL_DOT])    

def formatCurrency(currencyAmount, language):
    return str(currencyAmount[CurrencyField.FORMAT_PREFIX]) \
            + formatNumber(currencyAmount[CurrencyField.AMOUNT], currencyAmount[CurrencyField.DECIMAL_PLACES], language)  \
            + str(currencyAmount[CurrencyField.FORMAT_SUFFIX])

def formatCurrencies(currencyAmountList, langauge):
    if currencyAmountList is not None:
        return [formatCurrency(currencyAmount, langauge) for currencyAmount in currencyAmountList]
    else:
        return []

def formatItem(item, language):
    if item is not None:
        formatted = {}

        if ItemField.INITIAL_AMOUNT_IN_CURRENCY in item:
            formatted[ItemField.INITIAL_AMOUNT_IN_CURRENCY] = formatCurrencies(item[ItemField.INITIAL_AMOUNT_IN_CURRENCY], language)
        if ItemField.AMOUNT_IN_CURRENCY in item:
            formatted[ItemField.AMOUNT_IN_CURRENCY] = formatCurrencies(item[ItemField.AMOUNT_IN_CURRENCY], language)
        if ItemField.AMOUNT_IN_AUCTION_IN_CURRENCY in item:
            formatted[ItemField.AMOUNT_IN_AUCTION_IN_CURRENCY] = formatCurrencies(item[ItemField.AMOUNT_IN_AUCTION_IN_CURRENCY], language)

        item[ItemField.FORMATTED] = formatted

    return item
