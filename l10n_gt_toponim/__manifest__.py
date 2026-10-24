# -*- coding: utf-8 -*-

{
    'name': "Guatemalan module for Point of Sale",

    'summary': "Guatemalan module for Point of Sale",

    'description': """
        This module brings the technical requirement for the Guatemalan regulation.
        Install this if you are using the Point of Sale app in Guatemalan.    
        """,

    'category': 'Accounting/Localizations/Point of Sale',
    'version': '1.0',
    'depends': ['base', 'base_address_extended', 'sale', 'account'],
    'installable': True,
    'auto_install': True,
    'data': [
        'views/res_partner_views.xml',
        'views/address_data_views.xml',
        'security/ir.model.access.csv',
    ],
    'license': 'OEEL-1',
}
