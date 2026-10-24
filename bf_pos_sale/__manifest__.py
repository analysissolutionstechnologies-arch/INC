# -*- coding: utf-8 -*-

{
    'name': 'POS sale: not filter draft order',
    'version': '0.1',
    'author': 'Buildfish',
    'category': 'Point of Sale',
    'summary': 'POS sale: not filter draft order',
    'website': 'build-fish.com',
    'license': 'AGPL-3',
    'description': """
        POS sale: not filter draft order.
    """,
    'depends': ['pos_sale'],
    'data': [],
    'assets': {
        'point_of_sale._assets_pos': [
            'bf_pos_sale/static/src/**/*',
        ],
    },
    'price': 10.00,
    'currency': 'USD',
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'auto_install': False,
}
