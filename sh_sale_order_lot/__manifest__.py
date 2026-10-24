# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Sale Order Lot Selection",
    "author": "Softhealer Technologies",
    "website": "http://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Sales",
    "summary": """choose sale order line lot select sale order lot module lot assign to delivery app select quotation line lot odoo """,
    "description": """This module allows you to select a lot from the sale order line. On confirm of sale order it will automatically assign a lot to delivery order.
choose sale order line lot, select sale order lot module, lot assign to delivery app, select quotation line lot odoo""",
    "version": "0.0.1",
    "depends": [
        "sale_stock",
        "sale_management"
    ],
    "application": True,
    "data": [
        "views/sale_order_views.xml",
    ],
    "images": ["static/description/background.jpg", ],
    "auto_install": False,
    "installable": True,
    "license": "OPL-1",
    "price": 13,
    "currency": "EUR"
}
