# -*- coding: utf-8 -*-

from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    poe = fields.Float(string='POE', readonly=True)
    # poe_en_lineas = fields.Float(string='POE en Líneas', store=True)
    # poe_en_lineas_netfinance = fields.Float(string='POE en Líneas Netfinance',  store=True)
    # margen_netfinance = fields.Float(string='Margen Netfinance',   store=True)
    autorizacion_netfinance = fields.Char(string='Autorización Netfinance')
    poe_autorizado = fields.Float(string='POE Autorizado', store=True)
    Factura_monto_autorizado = fields.Char(string="Factura NETFINANCE", copy=False)
    update_total_verifica = fields.Boolean(string="Factura NETFINANCE", copy=False , store=True)
    
    
    
    update_total_verifica = fields.Boolean(string="Factura NETFINANCE", copy=False , compute='_compute_update_total_verifica', store=True)
    poe_en_lineas_netfinance = fields.Float(string='POE en Líneas Netfinance', compute='_compute_poe_en_lineas', store=False)
    margen_netfinance = fields.Float(string='Margen Netfinance', compute='_compute_margen_netfinance', store=False)
    poe_en_lineas = fields.Float(string='POE en Líneas', compute='_compute_poe_en_lineas', store=True)

    #hereda action_update_prices
    def action_update_prices(self):
        super(SaleOrder, self).action_update_prices()
        self._onchange_poe_order_line()
        
        # self.ensure_one()

        # self._recompute_prices()

        # if self.pricelist_id:
        #     message = _("Product prices have been recomputed according to pricelist %s.",
        #         self.pricelist_id._get_html_link())
        # else:
        #     message = _("Product prices have been recomputed.")
        # self.message_post(body=message)
    @api.depends('order_line.price_unit_netfinance', 'order_line.product_uom_qty', 'pricelist_id' ,'amount_total')
    def _compute_update_total_verifica(self):
        print("Ajustando _compute_update_total_verifica!!!!!!!!!" )
        for order in self:
            order.update_total_verifica = False
            for line in order.order_line:
                if line.price_unit_netfinance == line.price_unit:
                    line.price_unit = line.price_unit_netfinance
                    order.update_total_verifica = True
        
    def _compute_poe_en_lineas(self):
        for order in self:
            print("Ajustando _compute_poe_en_lineas!!!!!!!!!......................." )
            order.poe_en_lineas = 0
            order.poe_en_lineas_netfinance = 0
            # if order.pricelist_id and "CRÉDITO" in order.pricelist_id.name.lower():
            if order.pricelist_id and "CRÉDITO" == order.pricelist_id.name:
                # order.poe_en_lineas = sum(line.product_id.list_price * line.product_uom_qty for line in order.order_line)
                order.poe_en_lineas = sum(line.price_list * line.product_uom_qty for line in order.order_line)
                order.poe_en_lineas_netfinance = sum(line.price_unit * line.product_uom_qty for line in order.order_line)
                print("Ajustando _compute_poe_en_lineas!!!!!!!!!......................." , order.poe_en_lineas )
                print("Ajustando _compute_poe_en_lineas!!!!!!!!!......................." , order.poe_en_lineas_netfinance )
                print("TOTAL _compute_poe_en_lineas!!!!!!!!!......................." , order.amount_total )
  
  
    def _compute_margen_netfinance(self):
        for order in self:
            print("Ajustando _compute_margen_netfinance!!!!!!!!!===" )

            order.margen_netfinance = 0.0
            if order.Factura_monto_autorizado and order.Factura_monto_autorizado.replace('.', '', 1).isdigit():
                Factura_monto_autorizado = float(order.Factura_monto_autorizado)
                if order.pricelist_id and "CRÉDITO" == order.pricelist_id.name and Factura_monto_autorizado:
                    order.margen_netfinance = (Factura_monto_autorizado - order.poe_en_lineas) / (order.poe_en_lineas) if order.poe_en_lineas > 0 else 0
                    print("Ajustando _compute_margen_netfinance!!!!!!!!!===" ,order.margen_netfinance)
                    print("amount_total _compute_margen_netfinance!!!!!!!!!===" ,order.amount_total)
                    print("poe_en_lineas _compute_margen_netfinance!!!!!!!!!===" ,order.poe_en_lineas)

    @api.onchange('Factura_monto_autorizado', 'pricelist_id', 'order_line', 'order_line.product_uom_qty')
    def _onchange_poe_order_line(self):
        if self.pricelist_id and "CRÉDITO" == self.pricelist_id.name:
            _logger.info(" _onchange_poe_order_line?????? poe autorizado: %s", self.Factura_monto_autorizado)
            self._compute_poe_en_lineas()
            self._compute_margen_netfinance()
            self._adjust_price_units()
            _logger.info("FIN  _onchange_poe_order_line?????? ")
            

    def _adjust_price_units(self):
        for order in self:
            print("Ajustando precios de pedido _adjust_price_units" )
            if order.pricelist_id and "CRÉDITO" == order.pricelist_id.name:
                for line in order.order_line:
                    # line.price_unit = line.price_unit * (1 + order.margen_netfinance)
                    
                    if order.Factura_monto_autorizado and order.Factura_monto_autorizado.replace('.', '', 1).isdigit():
                        Factura_monto_autorizado = float(order.Factura_monto_autorizado)
                    line.price_unit = Factura_monto_autorizado * ( line.porcentaje_odoo_presente)