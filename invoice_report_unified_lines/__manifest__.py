# -*- coding: utf-8 -*-
{
    'name': 'Invoice Report Unified Lines',
    'author': 'Omar Flores - oflores@xetechs.com', 
    'website': 'https://www.xetechs.com',
    'category': 'Accounting',
    'license': 'LGPL-3',
    'version': '17.0',
    'description': 'Unificación de líneas de reportes de facturas',
    'depends': ['account', 'infilefel', 'point_of_sale'],
    'data': [
        'report/invoice_report.xml',
        'report/invoice_ticket_report.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'invoice_report_unified_lines/static/src/app/store/models.js',
        ],
    },
    'auto_install': False,
    'installable': True,
}
