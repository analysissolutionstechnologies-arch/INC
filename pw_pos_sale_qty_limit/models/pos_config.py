# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosConfig(models.Model):
    _inherit = 'pos.config'

    pw_restrict_sale_qty = fields.Boolean(string="Sales Qty Restriction")

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pw_restrict_sale_qty = fields.Boolean(related='pos_config_id.pw_restrict_sale_qty', readonly=False)


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_product_category(self):
        result = super(PosSession, self)._loader_params_product_category()
        result['search_params']['fields'] += ['pw_sale_limit', 'pw_max_qty']
        return result

    def _loader_params_product_product(self):
        result = super(PosSession, self)._loader_params_product_product()
        result['search_params']['fields'] += ['pw_sale_limit', 'pw_max_qty']
        return result
