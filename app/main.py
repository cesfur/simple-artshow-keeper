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
import flask
import netifaces
import os

ROOT_PATH = os.path.abspath(os.path.normpath(os.path.dirname(__file__)))

import config
config.load(os.path.normpath(os.path.join(ROOT_PATH, 'config.ini')))

from common.result import Result
from common.response import respondHtml, respondXml
from common.translate import registerDictionary
from common.phrase_dictionary import PhraseDictionary
from common.authentication import UserGroups, auth
from common.parameter import getParameter
from model.dataset import Dataset
from model.currency import Currency
from model.model import Model

from items import items_controller
from auction import auction_controller
from reconciliation import reconciliation_controller
from settings import settings_controller

# Configure logging
logging.basicConfig(
        filename=config.LOG_FILE,
        format='%(asctime)s | %(levelname)s | %(message)s',
        level=config.LOG_LEVEL)

# Configure paths
items_controller.ROOT_DIR_CUSTOM_DATA = config.CUSTOM_DATA_FOLDER
auction_controller.ROOT_DIR_CUSTOM_DATA = config.CUSTOM_DATA_FOLDER

# Configure flask
app = flask.Flask('Artshow')
app.root_path = ROOT_PATH
app.register_blueprint(items_controller.blueprint, url_prefix=items_controller.URL_PREFIX)
app.register_blueprint(auction_controller.blueprint, url_prefix=auction_controller.URL_PREFIX)
app.register_blueprint(reconciliation_controller.blueprint, url_prefix=reconciliation_controller.URL_PREFIX)
app.register_blueprint(settings_controller.blueprint, url_prefix=settings_controller.URL_PREFIX)
app.secret_key = config.SESSION_KEY

# Initialize application
dataset = Dataset(logging.getLogger('dataset'), config.DATA_FOLDER)
dataset.restore()
currency = Currency(logging.getLogger('currency'), dataset, currencyCodes=config.CURRENCY)
model = Model(
        logging.getLogger('model'), dataset,
        currency)
dictionaryPath = os.path.join(os.path.dirname(__file__), 'locale')
for language in config.LANGUAGES:
    registerDictionary(
            language,
            PhraseDictionary(
                    logging.getLogger('dictionary'),
                    os.path.join(dictionaryPath, 'translation.{0}.xml'.format(language))))
del dictionaryPath

@app.before_request
def before_request():
    flask.g.userGroup = UserGroups.UNKNOWN
    flask.g.language = config.DEFAULT_LANGUAGE
    flask.g.model = model

    localRequest = flask.request.remote_addr == '127.0.0.1'
    sessionID = flask.session.get('SessionID', None)
    if localRequest and model.findSession(sessionID):
        group, ip = model.getSessionUserInfo(sessionID)
        if ip != '127.0.0.1':
            print('Local session has been compomised by IP {0}. Resetting.'.format(ip))
            model.dropSession(sessionID)
            sessionID = None
        else:
            model.renewSession(sessionID)

    model.sweepSessions()

    if not model.findSession(sessionID):
        userGroup = UserGroups.ADMIN if localRequest else UserGroups.UNKNOWN
        sessionID = model.startNewSession(
            userGroup=userGroup,
            userIP=flask.request.remote_addr)
        flask.session['SessionID'] = sessionID
    else:
        model.updateSessionUserInfo(sessionID, userIP=flask.request.remote_addr)

    flask.g.sessionID = sessionID
    flask.g.userGroup, flask.g.userIP = model.getSessionUserInfo(sessionID)


@app.after_request
def after_request(response):
    if response.status_code / 100 == 2:
        flask.g.model.persist()
    return response
    
@app.route("/")
@auth(UserGroups.SCAN_DEVICE)
def index():
    return respondHtml('main', flask.g.userGroup, flask.g.language)

@app.route('/authenticate', methods=['GET', 'POST'])
def authenticate():
    nextUrl = getParameter('next')
    if nextUrl is None or nextUrl == '':
        nextUrl = flask.url_for('index')

    deviceCode = flask.g.model.generateDeviceCode(flask.g.sessionID)
    if deviceCode is None:
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.NO_DEVICE_CODE,
                'okTarget': flask.url_for('index')})
    else:
        return respondHtml('authenticate', flask.g.userGroup, flask.g.language, {
                'deviceCode': deviceCode,
                'doneTarget': nextUrl })


@app.errorhandler(Exception)
def catch_all(err):
    logging.getLogger('main').exception('Unhandled exception.')
    return respondHtml('message', flask.g.userGroup, flask.g.language, {
            'message': Result.CRITICAL_ERROR,
            'okTarget': flask.url_for('index')})

def run():
    print("Starting")
    localostOnly = False
    if localostOnly:
        app.run(debug=True, use_reloader=False) # Local address only
    else:
        ipAddresses = []
        for ifaceName in netifaces.interfaces():
            iface = netifaces.ifaddresses(ifaceName)
            if netifaces.AF_INET in iface:
                for addressInfo in iface[netifaces.AF_INET]:
                    address = addressInfo.get('addr', '127.0.0.1')
                    if address != '127.0.0.1':
                       ipAddresses.append(address)

        ipAddresses.sort()
        print('Allowed address:')
        for ipAddress in ipAddresses:
            print('   {0}'.format(ipAddress))
        app.run(host='0.0.0.0', debug=True, use_reloader=False) # Any address
    print("Finished")

if __name__ == "__main__":
    run()