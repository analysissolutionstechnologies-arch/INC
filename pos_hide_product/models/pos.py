# -*- coding: utf-8 -*-

from odoo import models, fields ,api


class ProductProduct(models.Model):
    _inherit = 'product.product' 
    
    hide_in_pos = fields.Boolean(string="Hide In POS")

class PosSession(models.Model):
    _inherit = 'pos.session'


    def _loader_params_product_product(self):
        result = super()._loader_params_product_product()
        result['search_params']['fields'].extend(['hide_in_pos'])
        return result