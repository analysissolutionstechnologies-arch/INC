from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    cantidad_disponible = fields.Float(string="Disponible", compute='_compute_cantidad_disponible', store=True)

    @api.depends('product_id','product_uom_qty' )
    def _compute_cantidad_disponible(self):
        """
        Método para calcular la cantidad disponible de cada producto
        basado en el almacén asignado a la orden de venta.
        """
        for line in self:
            if line.product_id and line.order_id.warehouse_id:
                # Obtener la ubicación del almacén asignado
                location = line.order_id.warehouse_id.lot_stock_id
                # Buscar las cantidades disponibles en la ubicación
                stock_quants = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=', location.id)
                ])
                # Sumar las cantidades disponibles, restando las reservadas
                line.cantidad_disponible = sum(quant.quantity - quant.reserved_quantity for quant in stock_quants)
            else:
                line.cantidad_disponible = 0.0








