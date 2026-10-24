# -*- coding: utf-8 -*-


{
    'name': 'INFILE FEL',
    'version': '17.0.1.1',
    'category': 'Localization',
    'summary': 'Módulo para facturacion en linea para Guatemala, Certificador Infile',
    'description': 'Módulo para facturacion en linea para Guatemala, Certificador Infile, maneja documentos de contingencia ',
    'sequence': '1',
    'website': 'https://www.erp-gt.com/',
    'author': 'ERP GT SYSTEMS',
    'maintainer': 'ERP GT SYSTEMS',
    'license': 'LGPL-3',
    'support': 'soporte@erp-gt.com',
    'depends': ['base','account'],
    'data': [
        'views/account_view.xml',
        'views/res_company_views.xml',
        'views/account_move_views.xml',
        'views/report_invoice.xml',
        'views/res_partner_view.xml',
        # 'views/report_invoice.xml',
        'views/reporte_ticket.xml',
        'data/paperformat_ticket.xml',
        'views/report.xml',
    ],
    'installable': True,
    'auto_install': False,
}
