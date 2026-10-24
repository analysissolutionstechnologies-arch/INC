# -*- coding: utf-8 -*-
# DP InfoSol PVT LTD. See LICENSE file for full copyright and licensing details.
{
    'name'       : 'Tarifas Netfinance Ajuste POE',
    'version'    : '17.0.1.1',
    "author"     : "Incomel, Cesar Augusto Chirinos",
    "support"    : "incomel.com",
    'category'   : 'Sale',
    'summary'    : '''Relacionar Facturas con ventas m2o.''',
    'description': '''Relacionar Facturas con ventas m2os.''',
    'depends'    : ['sale_management'],
    'data'       : [
                    'views/sale_order_view.xml',
                    ],
    'installable' : True,
    'auto_install': False,
}
