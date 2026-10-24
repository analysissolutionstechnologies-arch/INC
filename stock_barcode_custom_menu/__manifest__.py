# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom Barcode Menu Custom',
    'version': '1.0',
    'category': 'Inventory/Inventory',
    'summary': "Customize barcode menu views",
    'depends': ['stock_barcode', 'stock_barcode_picking_batch'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'stock_barcode_custom_menu/static/src/xml/main_menu.xml',
        ],
    },
    'auto_install': False,
    'license': 'OEEL-1',
}
