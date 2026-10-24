# -*- coding: utf-8 -*-
{
    "name": "POS Change Logo on POS Screen and Receipt | Change POS Logo",
    "version": "1.0",
    'summary': """
        This module is allow to set Logo on Screen and POS Receipt | Logo on POS Receipt and Screen | Change POS logo""",
    'description': """
        This module is allow to set Logo and Barocode on pos receipt
- POS Logo on Receipt
- Logo on pos Screen
        """,    
    "category": "Point Of Sale",
    'author': "Preway IT Solutions",
    "sequence": 2,
    "summary": "",
    "depends" : ["point_of_sale"],
    "data" : [
        "views/pos_config_view.xml",
    ],
    'qweb': ['static/src/xml/pos.xml'],
    'assets': {
        'point_of_sale._assets_pos': [
            'pw_pos_change_logo/static/src/js/Chrome.js',
            'pw_pos_change_logo/static/src/js/pos_store.js',
            'pw_pos_change_logo/static/src/xml/**/*',
        ],
    },
    'price': 7.0,
    'currency': 'EUR',
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
    "images":["static/description/Banner.png"],
}
