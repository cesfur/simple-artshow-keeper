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
import os
import shutil

class Datafile:
    def __init__(self, sourceFilename, testName):
        self.path = os.path.join(os.path.dirname(__file__), 'data')
        self.sourceFilename = os.path.join(self.path, sourceFilename)
        filename, fileExt = os.path.splitext(sourceFilename)
        self.testSpecificFilename = os.path.join(self.path, filename + testName + fileExt)
        
        shutil.copy(self.sourceFilename, self.testSpecificFilename)
        
    def clear(self):
        if os.path.isfile(self.testSpecificFilename):
            os.remove(self.testSpecificFilename)
        if os.path.isfile(self.testSpecificFilename + '.bak'):
            os.remove(self.testSpecificFilename + '.bak')
    
    def getFilename(self):
        return self.testSpecificFilename
