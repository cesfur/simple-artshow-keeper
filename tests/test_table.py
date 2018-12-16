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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.datafile import Datafile
from artshowkeeper.model.item import ItemField
from artshowkeeper.model.table import Table

class TestTable(unittest.TestCase):
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)

    def setUp(self):
        self.logger = logging.getLogger()
        self.dataFile = Datafile('test.model.items.xml', self.id())
        self.table = Table(self.logger, self.dataFile.getFilename(), 'ArtShowItems', 'Item', ItemField.ALL_PERSISTENT)

    def tearDown(self):
        self.dataFile.clear()
        del self.table
        
    def test_loadSave(self):
        self.assertTrue(self.table.load())
        self.table.save(True)
        self.assertTrue(self.table.load())
        
    def test_select(self):
        self.assertTrue(self.table.load())

        # Select exactly one row with a mandatory column that is not available
        rows = self.table.select(['Code', 'Title', 'Note'], 'Code == "A2"')
        self.assertEqual(1, len(rows))
        self.assertDictEqual({
                        'Title': 'Cougar',
                        'Code': 'A2',
                        'Note': None},
                rows[0]);
        self.assertFalse(self.table.changed(),
            'Table.Select: Run SELECT but the table is marked as changed')

        # Select all rows
        rows = self.table.select(['Code', 'Author'])
        self.assertTrue(len(rows) == self.table.len() and len(rows[0]) == 2,
            'Table.Select: Expected all rows with columns {Code, Author} but received %(row)s' % {'row': str(rows)})
        self.assertFalse(self.table.changed(),
            'Table.Select: Run SELECT but the table is marked as changed')

    def test_update(self):
        self.assertTrue(self.table.load())

        # Update row
        row = self.table.select(['Code', 'Title'], 'Code == "A2"')[0]
        numUpdated = self.table.update({'Title': 'ragouC'}, 'Code == "AXXX"')
        self.assertEqual(numUpdated, 0,
            'Table.Update: Updating a row (%(numUpdated)d) even though the row does not exist' % {'numUpdated': numUpdated})
        self.assertFalse(self.table.changed(),
            'Table.Update: Running UPDATE failed but the table is marked as changed')

        numUpdated = self.table.update({'Title': 'ragouC'}, 'Code == "A2"')
        rowUpdated = self.table.select(['Author', 'Title'], 'Code == "A2"')[0]
        self.assertTrue(numUpdated == 1 and row['Title'] == 'Cougar' and rowUpdated['Title'] == 'ragouC',
            'Table.Update: Updated row but the selecting the row returned %(row)s' % {'row': str(rowUpdated)})
        self.assertTrue(self.table.changed(),
            'Table.Update: Run UPDATE but the table is marked as not changed')

    def test_insert(self):
        self.assertTrue(self.table.load())

        insertedConflict = self.table.insert({'Code': 'A2', 'Title': 'Meow'}, 'Code')
        self.assertFalse(insertedConflict,
            'Table.Insert: Inserting a conflicting record did not fail')
        self.assertFalse(self.table.changed(),
            'Table.Insert: Running INSERT failed but the table is marked as changed')

        inserted = self.table.insert({'Code': 'A234', 'Title': 'Meow'}, 'Code')
        self.assertTrue(inserted,
            'Table.Insert: Inserting failed')
        self.assertTrue(self.table.changed(),
            'Table.Insert: Run INSERT but the table is marked as not changed')

        self.assertTrue(self.table.insert({'Code': 'A999'}, 'Code'))
        self.assertEqual(len(self.table.select('Code', 'Code == "A999" and Title is None')), 1)

    def test_delete(self):
        self.assertTrue(self.table.load())

        rowDelete = self.table.delete('Code == "A2503"')
        self.assertEqual(
                rowDelete, 0,
                'Table.Delete: Requested deleting a record that does not exist but it deleted %(num)d record(s).' % { 'num' : rowDelete })
        self.assertFalse(
                self.table.changed(),
                'Table.Delete: Running DELETE failed but the table is marked as changed')

        rowDelete = self.table.delete('Code == "A2"')
        self.assertEqual(
                rowDelete, 1,
                'Table.Delete: Requested deleting a record but it deleted %(num)d record(s).' % { 'num' : rowDelete })
        self.assertTrue(
                self.table.changed(),
                'Table.Delete: Run DELETE but the table is marked as not changed')
        rows = self.table.select(['Code', 'Title'], 'Code == "A2"')
        self.assertEqual(
                len(rows), 0,
                'Table.Delete: Deleted record selected ({0}).'.format(rows))

if __name__ == '__main__':
    unittest.main()
