# -*- coding: utf-8 -*-


{
    'name': 'POS TICKET FEL',
    'version': '17.0.1.1',
    'category': 'Localization',
    'summary': 'Módulo de complemento para emitir ticket certificado dentro del POS / Maneja Contingencia - Certificador INFILE',
    'description': 'Módulo de complemento para emitir ticket certificado dentro del POS / Maneja Contingencia - Certificador INFILE.',
    'sequence': '1',
    'website': 'https://www.erp-gt.com/',
    'author': 'ERP GT SYSTEMS',
    'maintainer': 'ERP GT SYSTEMS',
    'license': 'LGPL-3',
    'support': 'soporte@erp-gt.com',
    'depends': ['point_of_sale', 'web'],
    'data': [
        'views/templates.xml',
        'views/pos_order_view.xml',
    ],
'assets': {
        'point_of_sale.assets': [
            'pos_ticket_fel/static/src/js/Screens/ReceiptScreen/OrderReceipt.js',
            'pos_ticket_fel/static/src/js/Screens/qrcode.js',
            'pos_ticket_fel/static/src/js/Screens/screens.js',
            
        ],
        'web.assets_qweb': [
            'pos_ticket_fel/static/src/xml/Screens/ReceiptScreen/OrderReceipt.xml',
            'pos_ticket_fel/static/src/xml/Screens/ReceiptScreen/ClientDetailsEdit.xml',

        ],
},
    'installable': True,
    'auto_install': False,
}
