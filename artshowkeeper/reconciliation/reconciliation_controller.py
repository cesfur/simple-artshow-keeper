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
from datetime import datetime

from artshowkeeper.common.convert import *
from artshowkeeper.common.parameter import *
from artshowkeeper.common.response import respondHtml, respondXml
from artshowkeeper.common.result import Result
from artshowkeeper.common.authentication import auth, UserGroups
from artshowkeeper.model.item import ItemField
from artshowkeeper.model.summary import SummaryField, DrawerSummaryField, Summary

URL_PREFIX = '/reconciliation'
blueprint = flask.Blueprint('reconciliation', __name__, template_folder = 'templates', static_folder = 'static')

@blueprint.route('/', methods = ['GET', 'POST'])
def index():
    return flask.redirect(flask.url_for('index'))

@blueprint.route('/exit', methods = ['GET', 'POST'])
def exit():
    return flask.redirect(flask.url_for('index'))

@blueprint.route('/selectbadgetoreconciliate', methods = ['GET', 'POST'])
@auth()
def selectBadgeToReconciliate():
    return respondHtml(
            'findbadgetoreconciliate', flask.g.userGroup, flask.g.language, {
                'findTarget': flask.url_for('.startReconciliation'),
                'cancelledTarget': flask.url_for('.exit')})

def respondReconciliation(badge, summary, summaryChecksum):
    summary[SummaryField.AVAILABLE_UNSOLD_ITEMS].sort(key = lambda item: item[ItemField.SORT_CODE])
    summary[SummaryField.AVAILABLE_BOUGHT_ITEMS].sort(key = lambda item: item[ItemField.SORT_CODE])
    summary[SummaryField.DELIVERED_SOLD_ITEMS].sort(key = lambda item: item[ItemField.SORT_CODE])
    summary[SummaryField.PENDING_SOLD_ITEMS].sort(key = lambda item: item[ItemField.SORT_CODE])

    return respondHtml('reconciliation', flask.g.userGroup, flask.g.language, {
            'badge': badge,
            'summary': summary,
            'summaryChecksum': summaryChecksum,
            'printRunnerOverviewTarget': flask.url_for('.printRunnerOverview'),
            'reconciliateTarget': flask.url_for('.printReconciliation'),
            'cancelledTarget': flask.url_for('.selectBadgeToReconciliate')})

@blueprint.route('/startreconciliation', methods = ['GET', 'POST'])
@auth()
def startReconciliation():
    badge = getParameter('Badge')
    if toInt(badge) is None:
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.INVALID_BADGE,
                'badge': badge,
                'okTarget': flask.url_for('.selectBadgeToReconciliate')})
    else:
        summary = flask.g.model.getBadgeReconciliationSummary(badge)
        if summary is None:
            return respondHtml('message', flask.g.userGroup, flask.g.language, {
                    'message': Result.ERROR,
                    'okTarget': flask.url_for('.selectBadgeToReconciliate')})
        elif len(summary[SummaryField.AVAILABLE_UNSOLD_ITEMS]) == 0 and len(summary[SummaryField.AVAILABLE_BOUGHT_ITEMS]) == 0 and len(summary[SummaryField.DELIVERED_SOLD_ITEMS]) == 0 and len(summary[SummaryField.PENDING_SOLD_ITEMS]) == 0:
            return respondHtml('message', flask.g.userGroup, flask.g.language, {
                    'message': Result.BADGE_ALREADY_RECONCILIATED,
                    'badge': badge,
                    'okTarget': flask.url_for('.selectBadgeToReconciliate')})
        else:
            return respondReconciliation(badge, summary, Summary.calculateChecksum(summary))

@blueprint.route('/continuereconciliation', methods = ['GET', 'POST'])
@auth()
def continueReconciliation():
    badge = toInt(getParameter('Badge'))
    summaryChecksum = toInt(getParameter('SummaryChecksum'))
    summary = flask.g.model.getBadgeReconciliationSummary(badge)
    if summary is None:
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.ERROR,
                'okTarget': flask.url_for('.selectBadgeToReconciliate')})
    elif summaryChecksum != Summary.calculateChecksum(summary):
        logging.error('continueReconciliation: Reconciliation data changed.')
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.RECONCILIATION_DATA_CHANGED,
                'badge': badge,
                'okTarget': flask.url_for('.selectBadgeToReconciliate')})
    else:
        return respondReconciliation(badge, summary, summaryChecksum)

@blueprint.route('/printrunnedoverview', methods = ['GET', 'POST'])
@auth()
def printRunnerOverview():
    badge = toInt(getParameter('Badge'))
    summaryChecksum = toInt(getParameter('SummaryChecksum'))
    summary = flask.g.model.getBadgeReconciliationSummary(badge)
    if summary is None:
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.ERROR,
                'okTarget': flask.url_for('.selectBadgeToReconciliate')})
    elif summaryChecksum != Summary.calculateChecksum(summary):
        logging.error('printRunnerOverview: Reconciliation data changed.')
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.RECONCILIATION_DATA_CHANGED,
                'badge': badge,
                'okTarget': flask.url_for('.selectBadgeToReconciliate')})
    else:
        runnerItems = summary[SummaryField.AVAILABLE_UNSOLD_ITEMS] + summary[SummaryField.AVAILABLE_BOUGHT_ITEMS]
        runnerItems.sort(key = lambda item: item[ItemField.SORT_CODE])
        
        return respondHtml('runneroverview', flask.g.userGroup, flask.g.language, {
                'badge': badge,
                'items': runnerItems,
                'summaryChecksum': summaryChecksum,
                'printedTarget': flask.url_for('.continueReconciliation'),
                'cancelledTarget': flask.url_for('.continueReconciliation')})

@blueprint.route('/print', methods = ['GET', 'POST'])
@auth()
def printReconciliation():
    badge = toInt(getParameter('Badge'))
    summaryChecksum = toInt(getParameter('SummaryChecksum'))
    language = getParameter('Language') or flask.g.language
    summary = flask.g.model.getBadgeReconciliationSummary(badge)
    if summary is None:
        logging.error('printReconciliation: No summary data available for badge {0}.'.format(badge))
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.ERROR,
                'okTarget': flask.url_for('.selectBadgeToReconciliate')})
    elif summaryChecksum != Summary.calculateChecksum(summary):
        logging.error('printReconciliation: Reconciliation data changed for badge {0}.'.format(badge))
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.RECONCILIATION_DATA_CHANGED,
                'badge': badge,
                'okTarget': flask.url_for('.selectBadgeToReconciliate')})
    else:
        return respondHtml('receipt', flask.g.userGroup, language, {
                'badge': badge,
                'summary': summary,
                'summaryChecksum': summaryChecksum,
                'datetime': datetime.now(),
                'printedTarget': flask.url_for('.finalizeReconciliation'),
                'notprintedTarget': flask.url_for('.continueReconciliation'),
                'cancelledTarget': flask.url_for('.selectBadgeToReconciliate')})

@blueprint.route('/finalize', methods = ['GET', 'POST'])
@auth()
def finalizeReconciliation():
    badge = toInt(getParameter('Badge'))
    summaryChecksum = toInt(getParameter('SummaryChecksum'))
    summary = flask.g.model.getBadgeReconciliationSummary(badge)
    if summary is None:
        logging.error('finalizeReconciliation: No summary data available for badge {0}.'.format(badge))
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.ERROR,
                'okTarget': flask.url_for('.selectBadgeToReconciliate')})
    elif summaryChecksum != Summary.calculateChecksum(summary):
        logging.error('finalizeReconciliation: Reconciliation data changed for badge {0}.'.format(badge))
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.RECONCILIATION_DATA_CHANGED,
                'badge': badge,
                'okTarget': flask.url_for('.selectBadgeToReconciliate')})
    elif not flask.g.model.reconciliateBadge(badge):
        logging.error('reconciliate: Reconciliation failed for badge {0}.')
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.BADGE_RECONCILIATION_FAILED,
                'badge': badge,
                'okTarget': flask.url_for('.selectBadgeToReconciliate')})
    else:
        logging.info('reconciliate: Reconciliation succeeded for badge {0}.')
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.BADGE_RECONCILIATION_SUCCEEDED,
                'badge': badge,
                'okTarget': flask.url_for('.selectBadgeToReconciliate')})

@blueprint.route('/showsummary', methods = ['GET', 'POST'])
@auth()
def showSummary():
    summary = flask.g.model.getCashDrawerSummary()
    if summary is None:
        return respondHtml('message', flask.g.userGroup, flask.g.language, {
                'message': Result.ERROR,
                'okTarget': flask.url_for('.exit')})
    else:
        summary[DrawerSummaryField.BUYERS_TO_BE_CLEARED].sort(key = lambda actorSummary: actorSummary.Badge)
        summary[DrawerSummaryField.OWNERS_TO_BE_CLEARED].sort(key = lambda actorSummary: actorSummary.Badge)
        summary[DrawerSummaryField.PENDING_ITEMS].sort(key = lambda item: item[ItemField.SORT_CODE])
        return respondHtml('drawersummary', flask.g.userGroup, flask.g.language, {
                'summary': summary,
                'datetime': datetime.now(),
                'printedTarget': flask.url_for('.exit'),
                'cancelledTarget': flask.url_for('.exit')})
