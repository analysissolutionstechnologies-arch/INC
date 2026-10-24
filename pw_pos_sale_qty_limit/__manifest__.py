# -*- coding: utf-8 -*-
{
    'name': "POS Sale Quantity Limit | POS Sales Limit",
    'summary': """
        This module is allow to set sale quantity limit on product and product category | POS sale limit on product | Sale Qty limit on product category | POS Product sale limit""",
    'description': """
         This module is allow to set sale quantity limit on product and product category.""",    
    'version': '2.0',
    'author': "Preway IT Solutions",
    'category': 'Point of Sale',
    'depends': ['point_of_sale'],
    'data': [
        'views/product_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pw_pos_sale_qty_limit/static/src/js/ProductScreen.js',
        ],
    },
    'images':[
        'static/description/banner.png',
    ],
    'price': 15.0,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    "license": "LGPL-3",
    "images":["static/description/Banner.png"],
}
