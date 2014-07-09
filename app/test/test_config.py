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

from datafile import Datafile
import config

class TestConfig(unittest.TestCase):
    def setUpClass():
        logging.basicConfig(level=logging.DEBUG)

    def setUp(self):
        self.logger = logging.getLogger()
        self.configFile = Datafile('config.ini', self.id())

    def tearDown(self):
        self.configFile.clear()
        
    def test_loadConfig(self):
        config.load(self.configFile.getFilename())
        self.assertEqual(config.DEFAULT_LANGUAGE, 'cz')
        self.assertEqual(config.DATA_FOLDER, os.path.normpath(os.path.join(os.path.dirname(__file__), '../../data')))
        self.assertEqual(config.LOG_FILE, os.path.normpath('C:\\ProgramData\\Artshow\\artshow.log'))
        self.assertListEqual(config.CURRENCY, ['czk', 'eur', 'usd'])
        self.assertEqual(len(config.SESSION_KEY), 24)

if __name__ == '__main__':
    unittest.main()
