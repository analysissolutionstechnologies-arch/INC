# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name': 'POS Lock Screen | Point of Sale Auto Lock Timer',
    'version': '17.0.0.0',
    'category': 'Point Of Sale',
    'summary': 'Point of Sale Screen Auto Lock POS Screen Lock Timer Point of Sales Automatic Timer Lock POS Screen Lock Period Lock POS Period Point of Sale Lock Time Period POS Auto Lock Session Automatic POS Screen Lock Session POS Time Period Lock Auto POS Lock Period',
    'description' :"""POS Screen Lock Timer Odoo App helps users to automatically initiates a screen lock after specific time interval on POS terminal to safeguard sensitive information when it's idle, providing peace of mind and compliance with data protection regulations. Authorized users can easily unlock the screen with their credentials, user can also lock screen mannually by clicking lock icon on POS header. """,
    'author': 'BrowseInfo',
    'website': 'https://www.browseinfo.com/demo-request?app=bi_pos_auto_lock&version=17&edition=Community',
    "price": 20,
    "currency": 'EUR',
    'depends': ['base','point_of_sale'],
    'data': [
        'views/pos_view.xml',
    ],
    'assets': {
		'point_of_sale._assets_pos': [
            "bi_pos_auto_lock/static/src/css/pos.css",
            "bi_pos_auto_lock/static/src/js/pos_chrome.js",
		],
	},
    'license':'OPL-1',
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'live_test_url':'https://www.browseinfo.com/demo-request?app=bi_pos_auto_lock&version=17&edition=Community',
    "images":['static/description/POS-Screen-Lock-Timer.gif'],
}
