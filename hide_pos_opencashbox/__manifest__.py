# -*- coding: utf-8 -*-
{
    'name': "POS Hide Opening Cash Control",
    'summary': """Hide Pos Opening Cash Control Point of sale hide opening cash control pos hide opening cash control pos restrict opening cash control pos cash control restrictions hide pos cash control pos hide cash control restrict pos cash control hide opening cash controlHide Cash Control - Using this module Enable and Disable  restrict Opening Cash Control and Opening Cash Control. pos restrict cash control""",
    'description': """POS Hide Opening Cash Control""",
    'author': "Khaled Hassan",
    'website': "https://apps.odoo.com/apps/modules/browse?search=Khaled+hassan",
    'category': 'Point of Sale',
    'version': '17.0',
    'depends': ['point_of_sale'],
    'license': 'OPL-1',
    'currency': 'EUR',
    'price': '18',
    "images": ['static/description/main_screenshot.png'],
    'data': [
        'views/pos_config.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'hide_pos_opencashbox/static/src/js/HideCashBoxChrome.js',

        ],
    },

    'installable': True,
    'auto_install': False,
    'application': False,
}
