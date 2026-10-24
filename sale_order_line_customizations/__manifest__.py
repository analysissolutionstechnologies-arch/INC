# -*- coding: utf-8 -*-
{
    'name': 'Sale Order Line Customizations',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'Customizations for sale order line fields',
    'depends': [
        'sale_management',
        'sale_margin',
    ],
    'data': [
        'views/sale_order_line_customization_views.xml',
    ],
    'installable': True,
    'application': False,
}
