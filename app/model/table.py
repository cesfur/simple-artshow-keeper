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
import logging
import os
import codecs
import json
import xml.dom
from xml.dom import minidom
from common.convert import *

class Table:
    def __init__(self, logger, filename, tableName, rowName, columnNames):
        self.__logger = logger
        self.__filename = filename
        self.__filenameBak = self.__filename + '.bak'
        self.__filenameNew = self.__filename + '.new'
        self.__tableName = tableName
        self.__rowName = rowName
        self.__columnNames = columnNames
        self.__rows = []
        self.__changed = False
        
    def len(self):
        return len(self.__rows)
    
    def changed(self):
        return self.__changed
    
    def load(self):
        try:
            xmldoc = minidom.parse(self.__filename)
        except FileNotFoundError:
            self.__logger.warning(
                    'File "{0}" not found, keeping {1} rows.'.format(
                        self.__filename, len(self.__rows)))
            return True
        else:            
            if self.__tableName != xmldoc.documentElement.localName:
                self.__logger.error(
                        'Document root "{0}" does not match expected root "{1}"'.format(
                            xmldoc.documentElement.localName, self.__tableName))
                return False
            else:
                self.__rows = []
                for rowElement in xmldoc.documentElement.childNodes:
                    if rowElement.nodeType == xml.dom.Node.ELEMENT_NODE:
                        if self.__rowName != rowElement.localName:
                            self.__logger.error(
                                    'Skipping row "{0}" (value {1}) because it does not match expected row "{2}"'.format(
                                        rowElement.localName, rowElement.nodeValue, self.__rowName))
                        else:
                            row = {}
                            for colElement in rowElement.childNodes:
                                if colElement.nodeType == xml.dom.Node.ELEMENT_NODE:
                                    for value in colElement.childNodes:
                                        if value.nodeType == xml.dom.Node.TEXT_NODE:
                                            row[colElement.localName] = value.nodeValue
                            self.__normalizeRow(row)
                            self.__rows.append(row)
                            self.__logger.debug('Added row {0}'.format(json.dumps(row, cls=JSONDecimalEncoder)))
                self.__logger.info('Loaded {0} rows'.format(len(self.__rows)))
                self.__changed = False
                return True

    def __normalizeRow(self, row):
        """Normalize row by adding missing columns."""
        for colName in self.__columnNames:
            if colName not in row:
                row[colName] = None
    
    def save(self, forceSave = False):
        """Save the table if changed
        Args:
            forceSave: True to save regardless the table has been changed.
        """
        if not forceSave and not self.__changed:
            self.__logger.info('Not saving "{0}" because there has been no change.'.format(self.__filename))        
        else:
            # Save to DOM structure
            xmldoc = minidom.Document()
            docElement = xmldoc.createElement(self.__tableName)
            for row in self.__rows:
                rowElement = xmldoc.createElement(self.__rowName)
                numValidColums = 0
                for colName, colValue in row.items():
                    if colValue is not None and colName in self.__columnNames:
                        colElement = xmldoc.createElement(colName)
                        colElement.appendChild(xmldoc.createTextNode(str(colValue)))
                        rowElement.appendChild(colElement)
                        numValidColums = numValidColums + 1
                if numValidColums > 0:
                    docElement.appendChild(rowElement)
            xmldoc.appendChild(docElement)

            # Save to a new file
            encoding = 'utf-8'
            newFile = codecs.open(self.__filenameNew, encoding = encoding, mode = 'w')
            xmldoc.writexml(newFile, encoding = encoding)
            newFile.close()
            
            # Replace the original file
            try:
                os.remove(self.__filenameBak)
            except IOError:
                self.__logger.debug('No backup file "{0}" found.'.format(self.__filenameBak))
            try:
                os.renames(self.__filename, self.__filenameBak)
            except FileNotFoundError:
                self.__logger.debug('No current file "{0}" found.'.format(self.__filename))
            os.renames(self.__filenameNew, self.__filename)

            self.__logger.info('Saved {0} rows'.format(len(self.__rows)))

    def count(self, expression):
        """Similar to SQL:
        SELECT COUNT(*) FROM self WHERE expression
        Returns:
            A number of rows which qualifies to the expression.
        """
        resultCount = 0
        for row in self.__rows:
            if expression is None or eval(expression, {}, row):
                resultCount = resultCount + 1
        self.__logger.info('Counted {0} rows'.format(resultCount))
        return resultCount
        
    def select(self, colNames, expression = None):
        """Similar to SQL:
        SELECT colName FROM self WHERE expression
        Args:
            expression: Expression (e.g. 'Value is None') or None if any row qualifies.
        Returns:
            A list of selected items or an empty list if no item was selected.
        """
        result = []
        for row in self.__rows:
            if expression is None or eval(expression, {}, row):
                rowResult = {}
                for colName in colNames:
                    if colName in row:
                        rowResult[colName] = row[colName]
                    else:
                        rowResult[colName] = None
                result.append(rowResult)
        self.__logger.info('Selected {0} rows (expression: "{1}")'.format(len(result), expression))
        return result

    def update(self, values, expression):
        """Similar to SQL:
        UPDATE self SET values WHERE expression
        Returns:
            A number of affected rows.
        """
        updateCount = 0
        for row in self.__rows:
            try:
                if expression is None or eval(expression, {}, row):
                    for colName, colValue in values.items():
                        row[colName] = colValue
                    updateCount = updateCount + 1

            except NameError as e:
                self.__logger.warning('Evaluating expression "{0}" failed with "{1}" on a row "{2}. Skipping'.format(expression, str(e), row))

        if updateCount > 0:
            self.__changed = True

        self.__logger.info('Updated {0} rows'.format(updateCount))
        return updateCount

    def insert(self, values, primaryKey):
        """Similar to SQL:
        INSERT INTO self VALUE values
        Args:
            values: Dictionary. If column names are specified,
                missing columns are added with a value None.
            primaryKey: Column name which should not contain any duplicate.
        Returns:
            True if a new row was inserted.
        """
        if primaryKey is None or self.count('{0}=="{1}"'.format(primaryKey, toQuoteSafeStr(values[primaryKey]))) == 0:
            self.__normalizeRow(values)
            self.__rows.append(values)
            self.__changed = True
            self.__logger.info('Inserted one record')
            return True
        else:
            self.__logger.info('No record inserted due to a conflict')
            return False

    def delete(self, expression):
        """Similar to SQL:
        DELETE FROM self WHERE expression
        Returns:
            A number of affected rows.
        """
        deleteCount = 0
        newRows = []
        for row in self.__rows:
            if expression is None or eval(expression, {}, row):
                deleteCount = deleteCount + 1
            else:
                newRows.append(row)
        self.__rows = newRows

        if deleteCount > 0:
            self.__changed = True
        self.__logger.info('Deleted {0} rows'.format(deleteCount))
        return deleteCount
