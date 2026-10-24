# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    
    def _prepare_invoice_vals(self):
        self.ensure_one()
        vals = super(PosOrder, self)._prepare_invoice_vals()
        vals['invoice_origin'] = self.name
        search_sale = self.lines.mapped('sale_order_origin_id')
        

        # search_sale = self.env['sale.order'].search([('name', '=', self.name)] , limit=1)
        if search_sale:
            vals['sale_order_incomel_id'] = search_sale[0].id
        return vals