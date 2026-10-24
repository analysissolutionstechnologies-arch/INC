# from odoo import models, fields, api

# class StockPicking(models.Model):
#     _inherit = 'stock.picking'

#     x_bodega_origen = fields.Many2one('stock.warehouse', string='Bodega Origen', readonly=False, help="Bodega de origen inicial en la ruta.")

#     @api.model
#     def create(self, vals):
#         # Si 'location_id' está presente y 'x_bodega_origen' no está definido
#         if 'location_id' in vals and 'x_bodega_origen' not in vals:
#             location = self.env['stock.location'].browse(vals['location_id'])
#             # Buscar la bodega correspondiente a la ubicación de origen
#             warehouse = self.env['stock.warehouse'].search([('view_location_id', 'parent_of', location.id)], limit=1)
#             if warehouse:
#                 vals['x_bodega_origen'] = warehouse.id

#         # Si hay un valor 'origin', buscar el picking original para copiar la bodega origen
#         if 'origin' in vals and vals['origin']:
#             original_picking = self.env['stock.picking'].search([('name', '=', vals['origin'])], limit=1)
#             if original_picking and original_picking.x_bodega_origen:
#                 vals['x_bodega_origen'] = original_picking.x_bodega_origen.id

#         return super(StockPicking, self).create(vals)

# class StockMove(models.Model):
#     _inherit = 'stock.move'

#     x_bodega_origen = fields.Many2one('stock.warehouse', string='Bodega Origen', readonly=True)

#     @api.model
#     def create(self, vals):
#         move = super(StockMove, self).create(vals)
#         if move.picking_id and move.picking_id.x_bodega_origen:
#             move.x_bodega_origen = move.picking_id.x_bodega_origen
#         return move

from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_bodega_origen = fields.Many2one('stock.warehouse', string='Bodega Origen', readonly=False, help="Bodega de origen inicial en la ruta.")

    @api.model
    def create(self, vals):
        # Si 'location_id' está presente y 'x_bodega_origen' no está definido
        if 'location_id' in vals and 'x_bodega_origen' not in vals:
            location = self.env['stock.location'].browse(vals['location_id'])
            # Buscar la bodega correspondiente a la ubicación de origen
            warehouse = self.env['stock.warehouse'].search([('view_location_id', 'parent_of', location.id)], limit=1)
            if warehouse:
                vals['x_bodega_origen'] = warehouse.id

        # Si hay un valor 'origin', buscar el picking original para copiar la bodega origen y concatenar el valor del campo origin
        if 'origin' in vals and vals['origin']:
            original_picking = self.env['stock.picking'].search([('name', '=', vals['origin'])], limit=1)
            if original_picking:
                # Copiar el valor de x_bodega_origen
                if original_picking.x_bodega_origen:
                    vals['x_bodega_origen'] = original_picking.x_bodega_origen.id
                
                # Concatenar el campo origin del picking original con el nuevo origin
                vals['origin'] = f"{original_picking.origin or ''} - {vals['origin']}"

        return super(StockPicking, self).create(vals)

class StockMove(models.Model):
    _inherit = 'stock.move'

    x_bodega_origen = fields.Many2one('stock.warehouse', string='Bodega Origen', readonly=True)

    @api.model
    def create(self, vals):
        # Crear el movimiento de stock
        move = super(StockMove, self).create(vals)

        # Copiar la bodega origen del picking si está disponible
        if move.picking_id and move.picking_id.x_bodega_origen:
            move.x_bodega_origen = move.picking_id.x_bodega_origen

        return move















