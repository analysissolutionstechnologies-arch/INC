# -*- coding: utf-8 -*-
{
    'name': "Hide Button Export, Print, Import, Archive, Duplicate, Create, Edit, Delete, Action Buttons in Odoo 17",

    'summary': """
        Hide Button Export, Print, Import, Archive, Duplicate, Create, Edit, Delete, Action Buttons in Odoo 17
    """,

    'description': """
        Hide Button Export, Print, Import, Archive, Duplicate, Create, Edit, Delete, Action Buttons in Odoo 17
    """,

    'author': "Agung Sepruloh",
    'website': "https://github.com/agungsepruloh",
    'maintainers': ['agungsepruloh'],
    'license': 'OPL-1',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Extra Tools',
    'version': '17.0.1.0.2',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail'],

    # always loaded
    'data': [
        'views/res_users_views.xml',
    ],

    # only loaded in demonstration mode
    'demo': [],

    'assets': {
        'web.assets_backend': [
            'hide_show_action_buttons/static/src/js/action_menus.js',
            'hide_show_action_buttons/static/src/js/cog_menu.js',
            'hide_show_action_buttons/static/src/js/form_controller.js',
            'hide_show_action_buttons/static/src/js/kanban_controller.js',
            'hide_show_action_buttons/static/src/js/list_controller.js',
        ],
    },

    'images': ['static/description/banner.gif'],
    'application': True,
    'price': 12.00,
    'currency': 'USD',
}
