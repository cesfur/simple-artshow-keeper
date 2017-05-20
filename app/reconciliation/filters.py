import flask

from common.texttable import Texttable
from .reconciliation_controller import blueprint


# adds up to 36 - four columns are used as column separators
ID_WIDTH = 4
TEXT_WIDTH = 27
PRICE_WIDTH = 5
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
def unsold_table(items):
    """ format """
    return _tbl([[
        '#{}'.format(item['Code']),
        '{}'.format(item['Title']),
        '',
    ] for item in items])


@blueprint.app_template_filter('sold_table')
def sold_table(items, total, charity):
    return _tbl([[
        '#{}'.format(item['Code']),
        '{}\nBuyer: {}'.format(item['Title'], flask.g.model.getAttendee(item['Buyer'])),
        '{}€'.format(item['Amount']),
    ] for item in items] + [
        HLINE,
        ['', 'Total income', '{}€'.format(total)],
        ['', 'Charity contrib.', '{}€'.format(charity)],
        ['', 'Remaining', '{}€'.format(total - charity)],
    ])


@blueprint.app_template_filter('bought_table')
def bought_table(items, total):
    return _tbl([[
        '#{}'.format(item['Code']),
        '{}\nSeller: {}'.format(item['Title'], flask.g.model.getAttendee(item['Owner'])),
        '{}€'.format(item['Amount']),
    ] for item in items] + [
        HLINE,
        ['', 'Total', '{}€'.format(total)],
    ])


@blueprint.app_template_filter('cash_table')
def cash_table(total):
    rows = [
        ['', 'Collected', '{}€'.format(max(total, 0))],
        ['', 'Handed Over', '{}€'.format(min(total, 0))],
    ]
    return _tbl(rows)
