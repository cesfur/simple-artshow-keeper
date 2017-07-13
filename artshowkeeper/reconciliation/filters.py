import flask

from artshowkeeper.common.texttable import Texttable
from artshowkeeper.common.translate import translateString
from .reconciliation_controller import blueprint


# adds up to 36 - four columns are used as column separators
ID_WIDTH = 5
TEXT_WIDTH = 23
PRICE_WIDTH = 8
HLINE = ['-' * ID_WIDTH, '-' * TEXT_WIDTH, '-' * PRICE_WIDTH]


def _tbl(rows):
    t = Texttable()
    # we want to make our tables always look the same, so set static width
    t.set_cols_width([ID_WIDTH, TEXT_WIDTH, PRICE_WIDTH])
    # Texttable adds 1 space of padding left and right of all cells, plus one
    # character for vertical lines, even if VLINES is not set. In order to make
    # it not print just another space (adding up to three), replace VLINES char
    # by empty string
    t.set_deco(Texttable.VLINES)
    t.set_chars(['-', '', '+', '='])
    t.set_cols_align(['l', 'l', 'r'])
    # header gets printed differently, so skip
    t.add_rows(rows, header=False)
    return t.draw()


@blueprint.app_template_filter('unsold_table')
def unsold_table(items, language):
    """ format """
    return _tbl([[
        '{}{}'.format(translateString(language, '__Receipt.ItemNo'), item['Code']),
        '{}'.format(item['Title']),
        '',
    ] for item in items])


@blueprint.app_template_filter('sold_table')
def sold_table(items, total, charity, language):
    return _tbl([[
        '{}{}'.format(translateString(language, '__Receipt.ItemNo'), item['Code']),
        '{}\n{}: {}'.format(item['Title'], translateString(language, '__Receipt.Buyer'), flask.g.model.getAttendee(item['Buyer'])),
        '{}CZK'.format(item['Amount']),
    ] for item in items] + [
        HLINE,
        ['', translateString(language, '__Receipt.TotalIncome'), '{}CZK'.format(total)],
        ['', translateString(language, '__Receipt.CharityContribution'), '{}CZK'.format(charity)],
        ['', translateString(language, '__Receipt.Remaining'), '{}CZK'.format(total - charity)],
    ])


@blueprint.app_template_filter('bought_table')
def bought_table(items, total, language):
    return _tbl([[
        '{}{}'.format(translateString(language, '__Receipt.ItemNo'), item['Code']),
        '{}\n{}: {}'.format(item['Title'], translateString(language, '__Receipt.Seller'), flask.g.model.getAttendee(item['Owner'])),
        '{}CZK'.format(item['Amount']),
    ] for item in items] + [
        HLINE,
        ['', translateString(language, '__Receipt.Total'), '{}CZK'.format(total)],
    ])


@blueprint.app_template_filter('cash_table')
def cash_table(total, language):
    rows = [
        ['', translateString(language, '__Receipt.Collected'), '{}CZK'.format(max(total, 0))],
        ['', translateString(language, '__Receipt.HandedOver'), '{}CZK'.format(abs(min(total, 0)))],
    ]
    return _tbl(rows)
