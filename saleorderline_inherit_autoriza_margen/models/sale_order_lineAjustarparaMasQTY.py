# -*- coding: utf-8 -*-
from odoo import api, fields, models

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    price_list = fields.Float(string='Precio Lista', compute='_compute_price_list', store=True)
    price_unit_netfinance = fields.Float(string='Precio Unitario Netfinance', compute='_compute_price_unit_netfinance', store=True)
    diferencia_netfinance = fields.Float(string='Diferencia Netfinance', compute='_compute_diferencia_netfinance', store=True)
    porcentaje_netfinance = fields.Float(string='Porcentaje Netfinance', related='order_id.margen_netfinance', readonly=True)
    porcentaje_odoo_presente = fields.Float(string='Porcentaje Odoo',  readonly=True , compute='_compute_porcentaje_odoo_presente',)

    @api.depends('product_id', 'order_id.pricelist_id',  'product_uom_qty')
    def _compute_porcentaje_odoo_presente(self):
        for  line in self:
            mapear_total =  line.order_id.order_line.mapped('price_list')
            line.porcentaje_odoo_presente = (line.price_list) /  sum(mapear_total)
            
            
    
    # @api.depends('product_id', 'order_id.pricelist_id')
    # def _compute_price_list(self):
    #     for line in self:
    #         if line.order_id.pricelist_id:
    #             prices = line.order_id.pricelist_id._get_products_price(
    #                 products=line.product_id,
    #                 quantity=line.product_uom_qty,
    #                 date=line.order_id.date_order,
    #                 uom_id=line.product_uom
    #             )
    #             # Ensure we get the price for the specific product
    #             price_list = prices.get(line.product_id.id, line.product_id.list_price)
    #             line.price_list = price_list
    #         else:
    #             line.price_list = line.product_id.list_price

    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_price_list(self):
        for line in self:
            # check if there is already invoiced amount. if so, the price shouldn't change as it might have been
            # manually edited
            if line.qty_invoiced > 0 or (line.product_id.expense_policy == 'cost' and line.is_expense):
                continue
            if not line.product_uom or not line.product_id:
                line.price_list = 0.0
            else:
                line = line.with_company(line.company_id)
                price = line._get_display_price()
                line.price_list = line.product_id._get_tax_included_unit_price_from_price(
                    price,
                    line.currency_id or line.order_id.currency_id,
                    product_taxes=line.product_id.taxes_id.filtered(
                        lambda tax: tax.company_id == line.env.company
                    ),
                    fiscal_position=line.order_id.fiscal_position_id,
                )




    @api.depends('porcentaje_odoo_presente', 'order_id.pricelist_id', 'order_id.Factura_monto_autorizado', 'product_uom_qty', 'product_id')
    def _compute_price_unit_netfinance(self):
        for line in self:
            if line.order_id.pricelist_id and line.order_id.pricelist_id.name == "CRÉDITO":
                if line.porcentaje_odoo_presente:
                    order = line.order_id
                    if order.Factura_monto_autorizado and order.Factura_monto_autorizado.replace('.', '', 1).isdigit():
                        Factura_monto_autorizado = float(order.Factura_monto_autorizado)
                    line.price_unit_netfinance = Factura_monto_autorizado * ( line.porcentaje_odoo_presente)
                else:
                    line.price_unit_netfinance = line.price_list
                line.price_unit = line.price_unit_netfinance
            else:
                line.price_unit_netfinance = line.price_list
                

    # @api.depends('porcentaje_netfinance', 'order_id.pricelist_id', 'price_list')
    # def _compute_price_unit_netfinance(self):
    #     for line in self:
    #         if line.order_id.pricelist_id and line.order_id.pricelist_id.name == "CRÉDITO":
    #             if line.porcentaje_netfinance:
    #                 line.price_unit_netfinance = line.price_list * (1 + line.porcentaje_netfinance)
    #             else:
    #                 line.price_unit_netfinance = line.price_list
    #             line.price_unit = line.price_unit_netfinance
    #         else:
    #             line.price_unit_netfinance = line.price_list

    @api.depends('price_unit_netfinance', 'price_list')
    def _compute_diferencia_netfinance(self):
        for line in self:
            if line.order_id.pricelist_id and line.order_id.pricelist_id.name == "CRÉDITO":
                line.diferencia_netfinance = line.price_unit - line.price_list
            else:
                line.diferencia_netfinance = 0.0