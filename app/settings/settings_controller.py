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

from common.convert import *
from common.parameter import *
from common.response import respondHtml, respondXml
from common.result import Result
from model.item import ItemField
from controller.format import *

URL_PREFIX = '/settings'
blueprint = flask.Blueprint('settings', __name__, template_folder = 'templates', static_folder = 'static')

@blueprint.route('/', methods = ['GET', 'POST'])
def index():
    return flask.redirect(flask.url_for('index'))

@blueprint.route('/exit', methods = ['GET', 'POST'])
def exit():
    return flask.redirect(flask.url_for('index'))
    
@blueprint.route('/view', methods = ['GET', 'POST'])
def view():
    return respondHtml('viewsettings', flask.g.userGroup, flask.g.language, {
            'currencyInfo': flask.g.model.getCurrency().getInfo(),
            'saveSettingsTarget': flask.url_for('.saveApply'),
            'cancelledTarget': flask.url_for('.exit')})

@blueprint.route('/saveapply', methods = ['POST'])
def saveApply():
    currencyInfoList = flask.g.model.getCurrency().getInfo()
    for currencyInfo in currencyInfoList:
        amountInPrimary = getParameter("Currency_AmountInPrimary_{0}".format(currencyInfo[CurrencyField.CODE]))
        if amountInPrimary is None:
            logging.warning('saveApply: Currency {0} will not be updated because no new value has been supplied.'.format(currencyInfo[CurrencyField.CODE]))
        else:
            currencyInfo[CurrencyField.AMOUNT_IN_PRIMARY] = amountInPrimary

    result = flask.g.model.getCurrency().updateInfo(currencyInfoList)
    if result == Result.SUCCESS:
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': result,
                'okTarget': flask.url_for('.exit')})
    else:
        return respondHtml('viewsettings', flask.g.userGroup, flask.g.language, {
                'message': result,
                'currencyInfo': currencyInfoList,
                'saveSettingsTarget': flask.url_for('.saveApply'),
                'cancelledTarget': flask.url_for('.exit')})
