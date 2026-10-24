# -*- coding: utf-8 -*-
from odoo import api, fields, models

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"


    price_list = fields.Float(string='Precio Lista', related='product_id.list_price', readonly=True)
    price_unit_netfinance = fields.Float(string='Precio Unitario Netfinance', compute='_compute_price_unit_netfinance', store=True)
    diferencia_netfinance = fields.Float(string='Diferencia Netfinance', compute='_compute_diferencia_netfinance', store=True)
    porcentaje_netfinance = fields.Float(string='Porcentaje Netfinance', related='order_id.margen_netfinance', readonly=True)
  

    # @api.onchange('price_list', 'porcentaje_netfinance')
    # def _onchange_price_list_porcentaje_netfinance(self):
    #     self._compute_price_unit_netfinance()
    #     self._compute_diferencia_netfinance()

         


    # @api.depends(  'porcentaje_netfinance' , 'order_id.pricelist_id')
    @api.depends(  'porcentaje_netfinance', 'price_list' ) 
    def _compute_price_unit_netfinance(self):
        for line in self:
            if line.order_id.pricelist_id and line.order_id.pricelist_id.name == "CRÉDITO":
                if line.porcentaje_netfinance:
                    line.price_unit_netfinance = line.price_list * (1 + line.porcentaje_netfinance  )
                else:
                    line.price_unit_netfinance = line.price_list
                line.price_unit = line.price_unit_netfinance
            else:
                print("ELSEEEEEEEEEEEEEEEEEEEEEEEE")
                line.price_unit_netfinance = line.price_list


    @api.depends(    'price_unit_netfinance' )
    def _compute_diferencia_netfinance(self):
        for line in self:
            if line.order_id.pricelist_id and line.order_id.pricelist_id.name == "CRÉDITO":
                line.diferencia_netfinance = line.price_unit_netfinance - line.price_list
            else:
                line.diferencia_netfinance = 0.0