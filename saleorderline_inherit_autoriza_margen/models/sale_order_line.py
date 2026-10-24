# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    porcentaje_odoo_presente = fields.Float(string='Porcentaje Odoo', readonly=True, compute='_compute_porcentaje_odoo_presente')

    price_list = fields.Float(string='Precio Lista', compute='_compute_price_list', store=True)
    
    
    price_unit_netfinance = fields.Float(string='Precio Unitario Netfinance', compute='_compute_price_unit_netfinance', store=True)
    diferencia_netfinance = fields.Float(string='Diferencia Netfinance', compute='_compute_diferencia_netfinance', store=True)
    porcentaje_netfinance = fields.Float(string='Porcentaje Netfinance', related='order_id.margen_netfinance', readonly=True)

    @api.depends('product_id', 'order_id.pricelist_id', 'product_uom_qty')
    def _compute_porcentaje_odoo_presente(self):
        for line in self:
            mapear_total = line.order_id.order_line.mapped('price_list')
            total_price_list = sum(mapear_total)
            if total_price_list != 0:
                line.porcentaje_odoo_presente = (line.price_list * line.product_uom_qty) / total_price_list
            else:
                line.porcentaje_odoo_presente = 0.0

    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_price_list(self):
        for line in self:
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

    # @api.depends('porcentaje_odoo_presente', 'order_id.pricelist_id', 'order_id.Factura_monto_autorizado', 'product_uom_qty', 'product_id')
    def _compute_price_unit_netfinance(self):
        for line in self:
            if line.order_id.pricelist_id and line.order_id.pricelist_id.name == "CRÉDITO":
                order = line.order_id
                
                if not order.Factura_monto_autorizado:
                    raise ValidationError(_('Error: El monto autorizado de la factura no puede estar vacío para la lista de precios CRÉDITO.'))
                
                # Removemos la coma del número (ej: "2,570.44" -> "2570.44")
                monto_str = order.Factura_monto_autorizado.replace(',', '')
                monto_autorizado = float(monto_str)
                
                # Calculamos el precio unitario considerando la cantidad
                total_amount = monto_autorizado * line.porcentaje_odoo_presente
                line.price_unit_netfinance = total_amount / line.product_uom_qty if line.product_uom_qty else 0.0
                
                # except (ValueError, AttributeError):
                #     raise ValidationError(_('Error: El formato del monto autorizado no es válido. Debe ser un número (ejemplo: 2,570.44)'))
            
                line.price_unit = line.price_unit_netfinance
            else:
                line.price_unit_netfinance = line.price_unit

    @api.depends('price_unit_netfinance', 'price_list')
    def _compute_diferencia_netfinance(self):
        for line in self:
            if line.order_id.pricelist_id and line.order_id.pricelist_id.name == "CRÉDITO":
                line.diferencia_netfinance = line.price_unit_netfinance - line.price_list
            else:
                line.diferencia_netfinance = 0.0
