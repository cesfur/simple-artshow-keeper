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
import os

from artshowkeeper.common.convert import *
from artshowkeeper.common.parameter import *
from artshowkeeper.common.response import respondHtml, respondXml, respondCustomDataFile
from artshowkeeper.common.result import Result
from artshowkeeper.common.authentication import auth, UserGroups
from artshowkeeper.model.item import ItemField, ItemState
from artshowkeeper.controller.format import *

URL_PREFIX = '/auction'
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR_CUSTOM_DATA = None
blueprint = flask.Blueprint('auction', __name__, template_folder = 'templates', static_folder = 'static')

@blueprint.route('/', methods = ['GET', 'POST'])
def index():
    return flask.redirect(flask.url_for('index'))

@blueprint.route('/exit', methods = ['GET', 'POST'])
def exit():
    return flask.redirect(flask.url_for('index'))
    
@blueprint.route('/static/custom/<path:filename>', methods = ['GET'])
def getCustomFile(filename):
    return respondCustomDataFile(
            ROOT_DIR_CUSTOM_DATA,
            os.path.join(ROOT_DIR, blueprint.static_folder),
            filename,
            flask.g.language)

@blueprint.route('/list', methods = ['GET', 'POST'])
@auth(UserGroups.SCAN_DEVICE)
def listItems():
    items = flask.g.model.getAllItemsInAuction()
    items.sort(key=lambda item: item[ItemField.AUCTION_SORT_CODE])
    for item in items:
        imagePath, imageFilename, version = flask.g.model.getItemImage(item[ItemField.CODE])
        if imageFilename is not None:
            item[ItemField.IMAGE_URL] = flask.url_for('items.getImage', itemCode=item[ItemField.CODE], v=version)
        item[ItemField.EDIT_IMAGE_URL] = flask.url_for('.editAuctionItemImage', itemCode=item[ItemField.CODE])

    return respondHtml('listauctionitems', flask.g.userGroup, flask.g.language, {
        'items': items,
        'targetCancelled': flask.url_for('.exit'),
        'targetPrinted': '' })

@blueprint.route('/showstatus', methods = ['GET', 'POST'])
@auth()
def showStatus():
    return respondHtml('showStatus', flask.g.userGroup, flask.g.language, {})

@blueprint.route('/getstatus', methods = ['GET', 'POST'])
@auth()
def getStatus():
    item = formatItem(flask.g.model.getItemInAuction(), flask.g.language)
    if item is not None:
        itemCode = item[ItemField.CODE]
        imagePath, imageFilename, version = flask.g.model.getItemImage(itemCode)
        if imageFilename is not None:
            item[ItemField.IMAGE_URL] = flask.url_for('items.getImage', itemCode=itemCode, v=version)

    charityAmount = formatCurrencies(
            flask.g.model.getCurrency().convertToAllCurrencies(flask.g.model.getPotentialCharityAmount()),
            flask.g.language)
    
    return respondXml('getstatus', flask.g.userGroup, flask.g.language, {
        'item': item,
        'charity': charityAmount })

@blueprint.route('/auction', methods = ['GET', 'POST'])
@auth()
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
@auth()
def startAuctionItem():
    itemCode = getParameter('ItemCode')
    item = flask.g.model.sendItemToAuction(itemCode)
    if item is not None:
        return flask.redirect(flask.url_for('.auctionItem'))
    else:
        logging.warning('startAuctionItem: Cannot auction item "{0}".'.format(itemCode))
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.CANNOT_AUCTION_THIS_ITEM,
                'itemCode': itemCode,
                'okTarget': flask.url_for('.selectItemToAuction')})

@blueprint.route('/auctionitem', methods = ['GET', 'POST'])
@auth()
def auctionItem():
    item = flask.g.model.getItemInAuction()
    if item == None:
        logging.warning('auctionItem: No item selected to auction.')
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.INVALID_AUCTION_ITEM,
                'okTarget': flask.url_for('.selectItemToAuction')})
    else:
        item = formatItem(item, flask.g.language)
        return respondHtml('auctionitem', flask.g.userGroup, flask.g.language, {
                'item': item,
                'newAmountTarget': flask.url_for('.setNewAmount'),
                'auctionedTarget': flask.url_for('.finalizeItem'),
                'cancelledTarget': flask.url_for('.selectItemToAuction')})
 
@blueprint.route('/setnewamount', methods = ['GET', 'POST'])
@auth()
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
@auth()
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
@auth()
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
@auth()
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


@blueprint.route('/editimage/<itemCode>', methods=['GET'])
@auth(UserGroups.SCAN_DEVICE)
def editAuctionItemImage(itemCode):
    item = flask.g.model.getItem(itemCode)
    if item is None or item[ItemField.STATE] != ItemState.IN_AUCTION:
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.ITEM_NOT_FOUND,
                'itemCode': itemCode,
                'okTarget': flask.url_for('.listItems')})
    else:
        imagePath, imageFilename, version = flask.g.model.getItemImage(item[ItemField.CODE])
        if imageFilename is not None:
            item[ItemField.IMAGE_URL] = flask.url_for('items.getImage', itemCode=item[ItemField.CODE], v=version)

        return respondHtml('editauctionitemimage', flask.g.userGroup, flask.g.language, {
            'item': item,
            'targetCancelled': flask.url_for('.listItems'),
            'targetUpdated': flask.url_for('.updateAuctionItemImage', itemCode=item[ItemField.CODE]) })


@blueprint.route('/updateimage/<itemCode>', methods=['POST'])
@auth(UserGroups.SCAN_DEVICE)
def updateAuctionItemImage(itemCode):
    item = flask.g.model.getItem(getParameter('ItemCode'))
    imageFile = getParameter('ImageFile')
    if imageFile is not None and imageFile.filename == '':
        imageFile = None;

    if item is None or item[ItemField.STATE] != ItemState.IN_AUCTION:
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.ITEM_NOT_FOUND,
                'itemCode': itemCode,
                'okTarget': flask.url_for('.listItems')})
    else:
        result = flask.g.model.updateItemImage(itemCode, imageFile=imageFile)
        if result != Result.SUCCESS:
            return respondHtml('message', flask.g.userGroup, flask.g.language, {
                    'message': result,
                    'itemCode': itemCode,
                    'okTarget': flask.url_for('.editAuctionItemImage', itemCode=item[ItemField.CODE])})
        else:
            return flask.redirect(flask.url_for('.listItems'))
