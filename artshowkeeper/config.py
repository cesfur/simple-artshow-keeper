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
import sys
import os
import configparser
import binascii

__appDir = os.path.dirname(__file__)
LOG_LEVEL = logging.DEBUG

DEFAULT_LANGUAGE = 'en'
SESSION_KEY = '00'
DATA_FOLDER = '.'
CUSTOM_DATA_FOLDER = '.'
LOG_FILE = 'artshow.log'
CURRENCY = ['usd']
LANGUAGES = ['en']

def __normalize_path(path):
    if not os.path.isabs(path):
       path = os.path.join(__appDir, path)
    return os.path.normpath(path)

def __normalize_list(strList):
    return [element for element in strList if len(element) > 0]

def load(iniFile):
    global DEFAULT_LANGUAGE
    global SESSION_KEY
    global DATA_FOLDER
    global CUSTOM_DATA_FOLDER
    global LOG_FILE
    global CURRENCY
    global LANGUAGES

    if not os.path.isfile(iniFile):
        return

    config = configparser.ConfigParser()
    config.read(iniFile)

    DEFAULT_LANGUAGE = config['DEFAULT'].get('DEFAULT_LANGUAGE', DEFAULT_LANGUAGE)
    DATA_FOLDER = __normalize_path(config['DEFAULT'].get('DATA_FOLDER', DATA_FOLDER))
    CUSTOM_DATA_FOLDER = __normalize_path(config['DEFAULT'].get('CUSTOM_DATA_FOLDER', DATA_FOLDER))
    LOG_FILE = __normalize_path(config['DEFAULT'].get('LOG_FILE', LOG_FILE))
    CURRENCY = __normalize_list(config['DEFAULT'].get('CURRENCY', ','.join(CURRENCY)).split(','))
    LANGUAGES = __normalize_list(config['DEFAULT'].get('LANGUAGES', ','.join(LANGUAGES)).split(','))
    SESSION_KEY = binascii.unhexlify(config['DEFAULT'].get('SECRET_KEY', SESSION_KEY))
