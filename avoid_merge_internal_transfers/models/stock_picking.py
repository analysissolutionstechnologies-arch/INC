from odoo import models, api

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _assign_picking(self):
        """
        Sobrescribimos el método para evitar que las líneas de movimientos de stock se agrupen en un picking existente,
        pero solo en transferencias internas. Para cada picking se crea una nueva transferencia cuando sea necesario.
        """
        internal_picking_type = self.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1)

        for move in self:
            if move.state not in ('draft', 'cancel') and not move.picking_id:
                picking_type = move.picking_type_id

                # Verificamos si es una transferencia interna
                if picking_type == internal_picking_type:
                    # Creamos una nueva transferencia para todas las líneas del picking
                    location_dest_id = move.location_dest_id
                    location_id = move.location_id

                    # Crear una nueva transferencia interna (picking) en lugar de usar una existente
                    picking_vals = {
                        'picking_type_id': picking_type.id,
                        'location_id': location_id.id,
                        'location_dest_id': location_dest_id.id,
                        'origin': move.origin or '',
                        'move_type': 'direct',  # Ajustar según el caso
                    }

                    # Crear nuevo picking (transferencia)
                    new_picking = self.env['stock.picking'].create(picking_vals)

                    # Asignar el nuevo picking a todos los movimientos relacionados a este picking
                    moves_to_assign = self.search([('picking_type_id', '=', picking_type.id),
                                                   ('location_id', '=', location_id.id),
                                                   ('location_dest_id', '=', location_dest_id.id),
                                                   ('picking_id', '=', False)])
                    moves_to_assign.write({'picking_id': new_picking.id})
                else:
                    # Para otros tipos de transferencia, usar el comportamiento predeterminado
                    super(StockMove, self)._assign_picking()

        return True








