# -*- coding: utf-8 -*-
# DP InfoSol PVT LTD. See LICENSE file for full copyright and licensing details.
{
    'name'       : 'Autorizar Ventas desde Netfinance',
    'version'    : '16.0',
    "author"     : "Consulnet, Cesar Augusto Chirinos",
    "support"    : "consulnet.cl",
    'category'   : 'Sale',
    'summary'    : "Autorizar Ventas desde Netfinance",
    'description': "Autorizar Ventas desde Netfinance",
    'depends'    : ['sale_management', 'account' ,'base'],
    'data'       : [
                    'views/sale_order.xml',
                    'views/res_company.xml',
                    'views/account.xml',
                    'views/res_partner_views.xml',
                    ],
    'installable' : True,
    'auto_install': False,
}
