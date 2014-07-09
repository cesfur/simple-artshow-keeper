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

URL_PREFIX = '/auction'
blueprint = flask.Blueprint('auction', __name__, template_folder = 'templates', static_folder = 'static')

@blueprint.route('/', methods = ['GET', 'POST'])
def index():
    return flask.redirect(flask.url_for('index'))

@blueprint.route('/exit', methods = ['GET', 'POST'])
def exit():
    return flask.redirect(flask.url_for('index'))
    
@blueprint.route('/list', methods = ['GET', 'POST'])
def listItems():
    items = flask.g.model.getAllItemsInAuction()
    items.sort(key = lambda item: item[ItemField.SORT_CODE])
    
    return respondHtml('listauctionitems', flask.g.userGroup, flask.g.language, {
        'items': items,
        'targetCancelled': flask.url_for('.exit'),
        'targetPrinted': '' })

@blueprint.route('/showstatus', methods = ['GET', 'POST'])
def showStatus():
    return respondHtml('showStatus', flask.g.userGroup, flask.g.language, {})

@blueprint.route('/getstatus', methods = ['GET', 'POST'])
def getStatus():
    item = formatItem(flask.g.model.getItemInAuction(), flask.g.language)
    charityAmount = formatCurrencies(
            flask.g.model.convertToAllCurrencies(flask.g.model.getPotentialCharityAmount()),
            flask.g.language)
    
    return respondXml('getstatus', flask.g.userGroup, flask.g.language, {
        'item': item,
        'charity': charityAmount })

@blueprint.route('/auction', methods = ['GET', 'POST'])
def selectItemToAuction():
    flask.g.model.clearAuction()
    itemsToAuction = flask.g.model.getAllItemsInAuction()
    if len(itemsToAuction) <= 0:
        logging.warning('selectItemToAuction: No item to be auctioned.')
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.NO_ITEM_TO_AUCTION,
                'okTarget': flask.url_for('.exit')})
    else:
        itemsToAuction.sort(key = lambda item: item[ItemField.SORT_CODE])
        return respondHtml('finditemtoauction', flask.g.userGroup, flask.g.language, {
                'availableItems': itemsToAuction,
                'findTarget': flask.url_for('.startAuctionItem'),
                'cancelledTarget': flask.url_for('.exit')})

@blueprint.route('/startauctionitem', methods = ['GET', 'POST'])
def startAuctionItem():
    itemCode = getParameter('ItemCode')
    item = flask.g.model.sendItemToAuction(itemCode)
    if item != None:
        return flask.redirect(flask.url_for('.auctionItem'))
    else:
        logging.warning('startAuctionItem: Cannot auction item "{0}".'.format(itemCode))
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.CANNOT_AUCTION_THIS_ITEM,
                'itemCode': itemCode,
                'okTarget': flask.url_for('.selectItemToAuction')})

@blueprint.route('/auctionitem', methods = ['GET', 'POST'])
def auctionItem():
    item = flask.g.model.getItemInAuction()
    if item == None:
        logging.warning('auctionItem: No item selected to auction.')
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.INVALID_AUCTION_ITEM,
                'okTarget': flask.url_for('.selectItemToAuction')})
    else:
        return respondHtml('auctionitem', flask.g.userGroup, flask.g.language, {
                'item': item,
                'newAmountTarget': flask.url_for('.setNewAmount'),
                'auctionedTarget': flask.url_for('.finalizeItem'),
                'cancelledTarget': flask.url_for('.selectItemToAuction')})
 
@blueprint.route('/setnewamount', methods = ['GET', 'POST'])
def setNewAmount():
    newAmount = toDecimal(getParameter('NewAmount'))
    if newAmount == None or newAmount < 1:
        logging.warning('setNewAmount: Invalid amount {0}.'.format(newAmount or '<None>'))
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.INVALID_AMOUNT,
                'amount': newAmount,
                'okTarget': flask.url_for('.auctionItem')})

    elif not flask.g.model.updateItemInAuction(newAmount):
        logging.warning('setNewAmount: Updating failed.')
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.NEW_AMOUNT_FAILED,
                'okTarget': flask.url_for('.auctionItem')})

    else:
        return flask.redirect(flask.url_for('.auctionItem'))
    
@blueprint.route('/finalizeitem', methods = ['GET', 'POST'])
def finalizeItem():
    item = flask.g.model.getItemInAuction()
    if item == None:
        logging.warning('finalizeItem: No item in auction.')
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.INVALID_AUCTION_ITEM,
                'okTarget': flask.url_for('.selectItemToAuction')})
    else:
        return respondHtml('finalizeitem', flask.g.userGroup, flask.g.language, {
                'item': item,
                'sellUpdatedTarget': flask.url_for('.sellUpdatedItem'),
                'sellNoChangeTarget': flask.url_for('.sellItemNoUpdate'),                
                'cancelledTarget': flask.url_for('.auctionItem')})
    
@blueprint.route('/sellupdateditem', methods = ['GET', 'POST'])
def sellUpdatedItem():
    newBuyer = toInt(getParameter('NewBuyer'))
    item = flask.g.model.getItemInAuction()
    if item == None:
        logging.warning('sellUpdatedItem: No item in auction.')
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.INVALID_AUCTION_ITEM,
                'okTarget': flask.url_for('.selectItemToAuction')})
    elif newBuyer == None:
        logging.warning('sellUpdatedItem: Invalid buyer.')
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.INVALID_BUYER,
                'buyer': getParameter('NewBuyer'),
                'okTarget': flask.url_for('.finalizeItem')})
    elif not flask.g.model.sellItemInAuction(newBuyer):
        logging.warning('sellUpdatedItem: Updating failed.')
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.NEW_BUYER_FAILED,
                'buyer': newBuyer,
                'okTarget': flask.url_for('.finalizeItem')})
    else:
        return flask.redirect(flask.url_for('.selectItemToAuction'))

@blueprint.route('/sellitemnoupdate', methods = ['GET', 'POST'])
def sellItemNoUpdate():
    item = flask.g.model.getItemInAuction()
    if item == None:
        logging.warning('sellItemNoUpdate: No item in auction.')
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.INVALID_AUCTION_ITEM,
                'okTarget': flask.url_for('.selectItemToAuction')})
    elif not flask.g.model.sellItemInAuctionNoChange():
        logging.warning('sellItemNoUpdate: Updating failed.')
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.NEW_BUYER_FAILED,
                'okTarget': flask.url_for('.finalizeItem')})
    else:
        return flask.redirect(flask.url_for('.selectItemToAuction'))
        