# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api

class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    sale_warehouse_id = fields.Many2one('stock.warehouse',string="Sale Warehouse")
