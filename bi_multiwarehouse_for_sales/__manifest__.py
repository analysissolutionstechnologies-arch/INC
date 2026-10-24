# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name': "Sale Multi Warehouse Odoo App",
    'version': '17.0.0.0',
    'category': 'Sales',
    'summary': 'Sale order Multi Warehouse for sale order line multi warehouse sale order multiple warehouse sale order line by warehouse selection on sales multi warehouse sale line warehouse SO line warehouse selection on sale line multi warehouse option on sales',
    "description": """ This odoo app helps user to select multiple warehouse for sale order and create delivery order based on warehouse selected on sale order line, User have to select warehouse on product and on selecting product on sale order line warehouse will selected, user can also change warehouse. """,
    'author': 'Browseinfo',
    'website': "https://www.browseinfo.com/demo-request?app=bi_multiwarehouse_for_sales&version=17&edition=Community",
    "price": 19,
    "currency": 'EUR',
    'depends': ['base','stock','sale_management'],
    'data': [
        'views/sale_config_settings_views.xml',
        'views/product_template_inherit.xml',
        'views/product_product_inherit.xml',
        'views/sale_order_views.xml',
    ],
    "auto_install": False,
    "installable": True,
    "live_test_url" : 'https://www.browseinfo.com/demo-request?app=bi_multiwarehouse_for_sales&version=17&edition=Community',
    "images":['static/description/Banner.gif'],
    'license': 'OPL-1' ,
}
