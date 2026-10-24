# -*- coding: utf-8 -*-
{
    'name': 'INCOMEL Catálogo Público',
    'version': '17.0.2.19.0',
    'category': 'Website',
    'summary': 'Catálogo web público con stock, precios de efectivo y crédito.',
    'author': 'INCOMEL',
    'license': 'LGPL-3',
    'depends': [
        'website',
        'product',
        'sale',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_config_parameter.xml',
        'data/website_menu.xml',
        'views/product_template_views.xml',
        'views/catalog_config_views.xml',
        'views/catalogo_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
