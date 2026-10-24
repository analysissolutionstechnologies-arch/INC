# -*- coding: utf-8 -*-

{
    'name': 'POS Hide Invoice Button',
    'version': '1.0',
    'category': 'Point of Sale',
    'summary': 'POS hide Invoice, Point Of Sale hide Invoice, POS hide invoice print, POS disable Direct Print Invoice, hide print Invoice From pos, POS Invoice hide,POS Invoice disable',
    'description': """POS Direct Print Invoice""",
    'depends': ['point_of_sale'],
    'author': "Khaled Hassan",
    'website': "https://apps.odoo.com/apps/modules/browse?search=Khaled+hassan",
    'data': [
        'views/pos_config.xml',
    ],
    'version': '17.0',
    'license': 'OPL-1',
    'currency': 'EUR',
    'price': '8',
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'assets': {
        'point_of_sale._assets_pos': [
            "pos_hide_invoice_button/static/src/**/*.js",
        ],
    },
}
