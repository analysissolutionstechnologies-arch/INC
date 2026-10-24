# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductCategory(models.Model):
    _inherit = 'product.category'

    pw_sale_limit = fields.Boolean(string="POS Sale Limit")
    pw_max_qty = fields.Integer(string="Max Qty")


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pw_sale_limit = fields.Boolean('POS Sale Limit')
    pw_max_qty = fields.Float(string="Max Qty")
