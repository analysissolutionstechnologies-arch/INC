# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : crp@fidobe.com
#
##############################################################################
{
    "name": "POS Customer Validation",
    "version": "17.0.1.0",
    "summary": """POS Customer Validation""",
    "description": """POS Customer Validation""",
    "author": "Fidobe Solutions LLC",
    "category": "Point of Sale",
    "website": "https://www.fidobe.com",
    "depends": ["point_of_sale"],
    "data": [],
    "assets": {
        "point_of_sale._assets_pos": [
            "fs_pos_customer_validations/static/src/**/*",
        ],
    },
    "images": ["static/description/banner.gif"],
    "license": "LGPL-3",
    "installable": True,
    "application": True,
    "auto_install": False,
    "price": 0,
    "currency": "EUR",
}
