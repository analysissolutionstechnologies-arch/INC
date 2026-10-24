# -*- coding: utf-8 -*-

{
    'name': 'Pos Hide Products',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'author': 'ErpMstar Solutions',
    'summary': 'Allows you to hide (Discount, Coupon) products.',
    'description': "Allows you to hide (Discount, Coupon) products.",
    'depends': ['point_of_sale'],
    'data': [
        'views/views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_hide_product/static/src/**/*',
        ],
    },
    'images': [
        'static/description/pos.jpg',
    ],
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 10,
    'currency': 'EUR',
}
