# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields 
from odoo.exceptions import UserError
from odoo.tools import float_compare

class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    is_multiwarehouse = fields.Boolean(string='Multi Wahouse',default=False)

    def _action_confirm(self):
        res_config= self.env.company
        if res_config.allow_warehouse:
            wh_ids = []
            [wh_ids.append(x.warehouses_id) for x in self.order_line if x.warehouses_id not in wh_ids]
            for wh_id in wh_ids:
                so_lines = self.env['sale.order.line'].search([('warehouses_id', '=', wh_id.id), ('order_id', '=', self.id)])
        super(SaleOrderInherit, self)._action_confirm()
