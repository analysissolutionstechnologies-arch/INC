# -*- coding: utf-8 -*-
{
    'name': "POS validation cash out",
    'summary':  "POS restriction when withdrawing money from the cash register "
                "see money in cash when taking money from cash",
    'author': "CML",
    'website': "https://kaypi.pe",
    'category': 'tools',
    'version': '0.1',
    'license': 'LGPL-3',
    'depends': [
        'point_of_sale',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'cml_pos_cash_out_restrict/static/src/**/*',
        ],
    },
    'images': ["static/description/banner.png"],
    'qweb': [],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 10,
    'currency': 'USD',
}
