# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    'name': 'User Journal Restrictions',
    'version': '17.0.0.0',
    'category': 'Accounting',
    'summary': 'Restrict journal user access account journal restriction journal restriction for users restrict journal security journal restricted user journal restrictions accounting journal restriction users journal restriction user wise journal restrictions for users',
    "description": """
       
        User Journal Restrictions Odoo App helps users to restricting the journals for particular users. User have access to restrict journals and select allowed journals for that specific user. User can visible only allowed journals and visible only allowed users in specific journal. User can visible or use only allowed journal in payment.

    """,
    'author': 'BrowseInfo',
    "price": 15,
    "currency": 'EUR',
    'website': 'https://www.browseinfo.com',
    'depends': ['base', 'sale_management', 'account', 'stock', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'security/restrict_journal.xml',
        'views/journals_for_users.xml',
    ],
    'license':'OPL-1',
    'installable': True,
    'auto_install': False,
    'live_test_url':'https://youtu.be/fE23L0CovXc',
    "images":['static/description/User-Journal-Restrictions-Banner.gif'],
}
