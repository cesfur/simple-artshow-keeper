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
import werkzeug
import os

from common.convert import *
from common.parameter import *
from common.response import respondHtml, respondXml, respondCustomDataFile
from common.result import Result
from model.item import ItemField, ItemState
from controller.format import formatItem

URL_PREFIX = '/items'
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR_CUSTOM_DATA = None
blueprint = flask.Blueprint('items', __name__, template_folder='templates', static_folder='static')

@blueprint.route('/')
def index():
    return ""

@blueprint.route('/exit', methods = ['GET', 'POST'])
def exit():
    flask.g.model.dropImport(flask.g.sessionID)
    return flask.redirect(flask.url_for('index'))
    
@blueprint.route('/static/custom/<path:filename>', methods = ['GET'])
def getCustomFile(filename):
    return respondCustomDataFile(
            ROOT_DIR_CUSTOM_DATA,
            os.path.join(ROOT_DIR, blueprint.static_folder),
            filename,
            flask.g.language)

def __respondNewItemHtml(itemData, message=None):
    if itemData is None:
        itemData = { ItemField.FOR_SALE: True }
    elif ItemField.FOR_SALE not in itemData:
        itemData[ItemField.FOR_SALE] = ItemField.AMOUNT in itemData and ItemField.CHARITY in itemData
    return respondHtml('edititem', flask.g.userGroup, flask.g.language, {
            'item': itemData,
            'bidsheetsToPrint': True if len(flask.g.model.getAdded(flask.g.sessionID)) > 0 else False,
            'message': message,
            'cancelledTarget': flask.url_for('.exit'),
            'addNewTarget': flask.url_for('.addNewItem'),
            'importFileTarget': flask.url_for('.selectImportFile'),
            'printAddedTarget': flask.url_for('.printAddedItems') })
    
def __respondEditItemHtml(itemData, onUpdate, onCancel, message=None):
    if itemData is None:
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.ERROR,
                'okTarget': onCancel})
    else:
        if ItemField.FOR_SALE not in itemData:
            itemData[ItemField.FOR_SALE] = ItemField.AMOUNT in itemData and ItemField.CHARITY in itemData
        return respondHtml('edititem', flask.g.userGroup, flask.g.language, {
                'item': itemData,
                'message': message,
                'itemStates': ItemState.ALL,
                'amountSensitiveItemStates': ItemState.AMOUNT_SENSITIVE,
                'cancelledTarget': onCancel,
                'updateItemTarget': onUpdate })

@blueprint.route('/new')
def enterNewItem():
    flask.g.model.clearAdded(flask.g.sessionID)
    return __respondNewItemHtml(None, False)

@blueprint.route('/nextnew')
def enterNextNewItem():
    return __respondNewItemHtml(None, False)

@blueprint.route('/add', methods=['POST'])
def addNewItem():
    # Add the new item
    result = flask.g.model.addNewItem(
            flask.g.sessionID,
            owner=flask.request.form[ItemField.OWNER],
            author=flask.request.form[ItemField.AUTHOR],
            title=flask.request.form[ItemField.TITLE],
            medium=flask.request.form[ItemField.MEDIUM],
            amount=flask.request.form[ItemField.INITIAL_AMOUNT] if ItemField.FOR_SALE in flask.request.form else None,
            charity=flask.request.form[ItemField.CHARITY] if ItemField.FOR_SALE in flask.request.form else None,
            note=flask.request.form[ItemField.NOTE])

    # Show a result
    if result == Result.SUCCESS:
        nextItem = {
                ItemField.OWNER: flask.request.form.get(ItemField.OWNER, None),
                ItemField.AUTHOR: flask.request.form.get(ItemField.AUTHOR, None),
                ItemField.FOR_SALE: True }
    else:
        nextItem = flask.request.form
    return __respondNewItemHtml(nextItem, result)
 
@blueprint.route('/printadded', methods=['GET', 'POST'])
def printAddedItems():
    addedItems = flask.g.model.getAddedItems(flask.g.sessionID)
    if len(addedItems) == 0:
        logging.warning('printAdded: No items to be printed. Returning back to the adding the item.')
        return __respondNewItemHtml(None, Result.NOTHING_TO_PRINT)
    else:
        logging.debug('printAdded: Printing %(numItems)d item(s).' % { 'numItems': len(addedItems) })
        addedItems[:] = [formatItem(item, flask.g.language) for item in addedItems]
        return respondHtml('bidsheets', flask.g.userGroup, flask.g.language, {
                'items': addedItems,
                'cancelledTarget': flask.url_for('.printAddedCancelled'),
                'printedTarget': flask.url_for('.printAddedPrinted')})

@blueprint.route('/printaddedcancel', methods=['GET', 'POST'])
def printAddedCancelled():
    logging.debug('printAddedCancelled: Printing cancelled.')
    return __respondNewItemHtml(None, Result.PRINT_CANCELLED)
                
@blueprint.route('/printaddedprinted', methods=['GET', 'POST'])
def printAddedPrinted():
    flask.g.model.clearAdded(flask.g.sessionID)
    return __respondNewItemHtml(None)
        
@blueprint.route('/list', methods=['GET', 'POST'])
def listItems():
    items = flask.g.model.getAllItems()
    items.sort(key = lambda item: item[ItemField.SORT_CODE])

    return respondHtml('listitems', flask.g.userGroup, flask.g.language, {
        'items': items,
        'targetEditItem_Raw': '.editItem',
        'targetCancelled': flask.url_for('.exit'),
        'targetPrintSelected': flask.url_for('.printSelectedItems'),
        'targetDeleteSelected': flask.url_for('.deleteSelectedItems') })

def __getSelectedItemCodes(form):
    if 'SelectedItemCodes' in form:
        return [code for code in form['SelectedItemCodes'].split(',') if len(code) > 0]
    else:
        return []

@blueprint.route('/printmultiple', methods=['GET', 'POST'])
def printSelectedItems():
    itemCodes = __getSelectedItemCodes(flask.request.form)

    logging.debug('printSelectedItems: Requested to print %(cnt)d item(s): %(items)s' % {'cnt': len(itemCodes), 'items': ','.join(itemCodes)})

    if len(itemCodes) > 0:
        selectedItems = flask.g.model.getItems(itemCodes)
        selectedItems[:] = [formatItem(item, flask.g.language) for item in selectedItems]
        return respondHtml('bidsheets', flask.g.userGroup, flask.g.language, {
                'items': selectedItems,
                'cancelledTarget': flask.url_for('.listItems'),
                'printedTarget': flask.url_for('.listItems') })
    else:
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.NO_ITEMS_SELECTED,
                'okTarget': flask.url_for('.listItems')})

@blueprint.route('/deletemultiple', methods = ['POST'])
def deleteSelectedItems():
    itemCodes = __getSelectedItemCodes(flask.request.form)

    logging.debug('deleteSelectedItems: Requested to delete %(cnt)d item(s): %(items)s' % {'cnt': len(itemCodes), 'items': ','.join(itemCodes)})

    if len(itemCodes) > 0:
        flask.g.model.deleteItems(itemCodes)
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.ITEMS_DELETED,
                'itemCode' : ', '.join(itemCodes),
                'okTarget': flask.url_for('.listItems')})
    else:
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.NO_ITEMS_SELECTED,
                'okTarget': flask.url_for('.listItems')})

@blueprint.route('/edit/<itemCode>', methods=['POST', 'GET'])
def editItem(itemCode):
    item = flask.g.model.getItem(itemCode)
    if item is None:
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.ITEM_NOT_FOUND,
                'itemCode': itemCode,
                'okTarget': flask.url_for('.listItems')})
    else:
        return __respondEditItemHtml(
                item,
                onUpdate=flask.url_for('.updateItem', itemCode=itemCode),
                onCancel=flask.url_for('.listItems'),
                message=None)

@blueprint.route('/update/<itemCode>', methods=['POST'])
def updateItem(itemCode):
    item = flask.g.model.getItem(getParameter('ItemCode'))
    if item is None:
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.ITEM_NOT_FOUND,
                'itemCode': itemCode,
                'okTarget': flask.url_for('.listItems')})
    else:
        result = flask.g.model.updateItem(
                itemCode,
                owner=flask.request.form[ItemField.OWNER],
                author=flask.request.form[ItemField.AUTHOR],
                title=flask.request.form[ItemField.TITLE],
                medium=flask.request.form[ItemField.MEDIUM],
                state=flask.request.form[ItemField.STATE],
                initialAmount=flask.request.form[ItemField.INITIAL_AMOUNT],
                charity=flask.request.form[ItemField.CHARITY],
                amount=flask.request.form[ItemField.AMOUNT],
                buyer=flask.request.form[ItemField.BUYER],
                note=flask.request.form[ItemField.NOTE])

        if result not in [Result.SUCCESS, Result.NOTHING_TO_UPDATE]:
            itemData = flask.request.form.copy()
            itemData[ItemField.CODE] = itemCode;
            return __respondEditItemHtml(
                    itemData,
                    onUpdate=flask.url_for('.updateItem', itemCode=itemCode),
                    onCancel=flask.url_for('.listItems'),
                    message=result)
        else:
            return flask.redirect(flask.url_for('.listItems'))

@blueprint.route('/close', methods = ['GET', 'POST'])
def selectItemToClose():
    clearPersistetParameter('ItemCode')
    closableItems = flask.g.model.getAllClosableItems()
    closableItems.sort(key = lambda item: item[ItemField.SORT_CODE])
    if len(closableItems) > 0:
        return respondHtml('finditemtoclose', flask.g.userGroup, flask.g.language, {
                'availableItems': closableItems,
                'findTarget': flask.url_for('.updateItemToClose'),
                'cancelledTarget': flask.url_for('.exit')})
    else:
        logging.warning('closeItem: No displayed item found.')
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.NO_ITEM_TO_CLOSE,
                'okTarget': flask.url_for('.exit')})

@blueprint.route('/closeupdate', methods = ['GET', 'POST'])
def updateItemToClose():
    itemCode = getParameter('ItemCode')
    item = flask.g.model.getItem(itemCode)

    if itemCode is None:
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.INVALID_ITEM_CODE,
                'okTarget': flask.url_for('.selectItemToClose')})
    elif item is None:
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.ITEM_NOT_FOUND,
                'itemCode': itemCode,
                'okTarget': flask.url_for('.selectItemToClose')})
    elif not flask.g.model.isItemClosable(item):
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.ITEM_NOT_CLOSABLE,
                'itemCode': itemCode,
                'okTarget': flask.url_for('.selectItemToClose')})
    else:
        persistParameter('ItemCode', itemCode)
        return respondHtml('updateitemtoclose', flask.g.userGroup, flask.g.language, {
                'item': item,
                'notSoldTarget': flask.url_for('.closeItemAsNotSold'),
                'soldTarget': flask.url_for('.closeItemAsSold'),
                'toAuctionTarget': flask.url_for('.closeItemIntoAuction'),
                'cancelledTarget': flask.url_for('.selectItemToClose')})

@blueprint.route('/closenotsold', methods = ['GET', 'POST'])
def closeItemAsNotSold():
    itemCode = getParameter('ItemCode')
    result = flask.g.model.closeItemAsNotSold(itemCode)
    if result != Result.SUCCESS:
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': result,
                'okTarget': flask.url_for('.updateItemToClose')})
    else:
        return flask.redirect(flask.url_for('.selectItemToClose'))

@blueprint.route('/closesold', methods = ['GET', 'POST'])
def closeItemAsSold():
    itemCode = getParameter('ItemCode')
    amount = getParameter('Amount')
    buyer = getParameter('Buyer')

    result = flask.g.model.closeItemAsSold(itemCode, amount = amount, buyer = buyer)
    if result != Result.SUCCESS:
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': result,
                'buyer': buyer,
                'amount': amount,
                'minAmount': flask.g.model.getItem(itemCode)[ItemField.INITIAL_AMOUNT] if result == Result.AMOUNT_TOO_LOW else None,
                'okTarget': flask.url_for('.updateItemToClose')})
    else:
        return flask.redirect(flask.url_for('.selectItemToClose'))

@blueprint.route('/closeauction', methods = ['GET', 'POST'])
def closeItemIntoAuction():
    itemCode = getParameter('ItemCode')
    amount = getParameter('Amount')
    buyer = getParameter('Buyer')
    imageFile = getParameter('ImageFile')
    if imageFile is not None and imageFile.filename == '':
        imageFile = None;

    result = flask.g.model.closeItemIntoAuction(itemCode, amount=amount, buyer=buyer, imageFile=imageFile)
    if result != Result.SUCCESS:
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': result,
                'buyer': buyer,
                'amount': amount,
                'minAmount': flask.g.model.getItem(itemCode)[ItemField.INITIAL_AMOUNT] if result == Result.AMOUNT_TOO_LOW else None,
                'okTarget': flask.url_for('.updateItemToClose')})
    else:
        return flask.redirect(flask.url_for('.selectItemToClose'))


@blueprint.route('/image/<itemCode>', methods=['GET'])
def getImage(itemCode):
    imagePath, imageFilename = flask.g.model.getItemImage(itemCode)
    if imageFilename is None:
        flask.abort(404)
    else:
        return respondCustomDataFile(None, imagePath, imageFilename, None);

@blueprint.route('/editauctionimage', methods=['GET'])
def editAuctionImage():
    itemCode = getParameter('ItemCode')
    item = flask.g.model.getItem(itemCode)
    if item is None:
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.NOTHING_TO_UPDATE,
                'itemCode': itemCode,
                'okTarget': flask.url_for('.selectItemToClose')})
    else:
        return respondHtml('edititemimage', flask.g.userGroup, flask.g.language, {
                'item': item,
                'saveTarget': flask.url_for('.updateAuctionImage', ItemCode=itemCode),
                'cancelledTarget': flask.url_for('.selectItemToClose'),
                'cancelledTargetTitle': '__EditItemImage.Skip'})

@blueprint.route('/updateauctionimage', methods=['POST'])
def updateAuctionImage():
    itemCode = getParameter('ItemCode')
    result = flask.g.model.updateItemImage(itemCode, getParameter('ImageData'))
    if result != Result.SUCCESS:
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': result,
                'itemCode': itemCode,
                'okTarget': flask.url_for('.editAuctionImage', ItemCode=itemCode)})
    else:
        return flask.redirect(flask.url_for('.editAuctionImage', ItemCode=itemCode))#DEBUG
        #return flask.redirect(flask.url_for('.selectItemToClose'))#DEBUG


@blueprint.route('/importdone', methods = ['GET', 'POST'])
def leaveImport():
    flask.g.model.dropImport(flask.g.sessionID)
    return flask.redirect(flask.url_for('.enterNextNewItem'))

@blueprint.route('/selectimport', methods = ['GET', 'POST'])
def selectImportFile():
    flask.g.model.dropImport(flask.g.sessionID)
    return respondHtml('selectimportfile', flask.g.userGroup, flask.g.language, {
            'targetUploadFile': flask.url_for('.uploadImportFile'),
            'targetUploadText': flask.url_for('.uploadImportText'),
            'targetCancelled': flask.url_for('.leaveImport')})

@blueprint.route('/uploadimportfile', methods = ['POST'])
def uploadImportFile():
    # 1. Retrieve input.
    file = flask.request.files.get('ImportFile', None)
    if file is None:
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.INVALID_FILE,
                'okTarget': flask.url_for('.leaveImport')})

    # 2. Load import.
    importedItems, importedChecksum = flask.g.model.importCSVFile(flask.g.sessionID, file.stream)

    # 3. Present result.
    return respondHtml('approveimport', flask.g.userGroup, flask.g.language, {
            'importItems': importedItems,
            'importChecksum': importedChecksum,
            'importFilename': werkzeug.utils.secure_filename(file.filename),
            'importRequiresOwner': not flask.g.model.isOwnerDefinedInImport(importedItems),
            'targetApproved': flask.url_for('.applyImport'),
            'targetChangeFile': flask.url_for('.selectImportFile'),
            'targetCancelled': flask.url_for('.leaveImport')})

@blueprint.route('/uploadimporttext', methods = ['POST'])
def uploadImportText():
    # 1. Retrieve input.
    text = getParameter('ImportText')
    if text is None:
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.INVALID_FILE,
                'okTarget': flask.url_for('.leaveImport')})

    # 2. Load import.
    importedItems, importedChecksum = flask.g.model.importText(flask.g.sessionID, text)

    # 3. Present result.
    return respondHtml('approveimport', flask.g.userGroup, flask.g.language, {
            'importItems': importedItems,
            'importChecksum': importedChecksum,
            'importRequiresOwner': not flask.g.model.isOwnerDefinedInImport(importedItems),
            'targetApproved': flask.url_for('.applyImport'),
            'targetChangeFile': flask.url_for('.selectImportFile'),
            'targetCancelled': flask.url_for('.leaveImport')})

@blueprint.route('/applyimport', methods = ['POST'])
def applyImport():
    # 1. Retrieve input.
    checksum = getParameter('ImportChecksum')
    owner = getParameter('Owner')

    # 2. Apply import.
    result, skippedItems, renumberedItems = flask.g.model.applyImport(flask.g.sessionID, checksum, owner)

    # 3. Present result.
    if result != Result.SUCCESS or (len(skippedItems) == 0 and len(renumberedItems) == 0):
        return __respondNewItemHtml(None, message=result)
    else:
        return respondHtml('reportimport', flask.g.userGroup, flask.g.language, {
                'skippedItems': skippedItems,
                'renumberedItems': renumberedItems,
                'targetContinue': flask.url_for('.leaveImport')})
