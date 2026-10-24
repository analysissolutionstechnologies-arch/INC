# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    poe_autorizado = fields.Float(string='POE Autorizado', store=True)
    Factura_monto_autorizado = fields.Char(string="Factura NETFINANCE", copy=False)
    margen_netfinance = fields.Float(string='Margen Netfinance', compute='_compute_margen_netfinance', store=False)

#    @api.constrains('poe_autorizado', 'order_line')
#    def _validar_poe(self):
#        for order in self:
#            if order.pricelist_id and order.pricelist_id.name == "CRÉDITO":
#                total_poe = sum(line.price_list * line.product_uom_qty for line in order.order_line)
#                if abs(total_poe - order.poe_autorizado) > 0.01:
#                    raise ValidationError(_('El total del POE debe coincidir con el POE autorizado'))

    @api.depends('Factura_monto_autorizado', 'order_line.price_list', 'pricelist_id',
                 'order_line.price_unit_netfinance', 'order_line.product_uom_qty',
                 'order_line.price_unit')
    def _compute_margen_netfinance(self):
        for order in self:
            order.margen_netfinance = 0.0
            if ( order.pricelist_id and 
                order.pricelist_id.name == "CRÉDITO" and 
                order.Factura_monto_autorizado ):
                
                monto_factura = float(order.Factura_monto_autorizado)
                total_poe = sum(line.price_list * line.product_uom_qty for line in order.order_line)
                
                if total_poe > 0:
                    order.margen_netfinance = (monto_factura - total_poe) / total_poe
                
                for line in order.order_line:
                    line._compute_price_unit_netfinance()
                    line.price_unit = line.price_unit_netfinance
