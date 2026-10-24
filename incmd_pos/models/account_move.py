from odoo import models, api

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    @api.model_create_multi
    def create(self, vals_list):
        # Crear las facturas normalmente
        moves = super().create(vals_list)
        
        # Para cada factura creada
        for move in moves:
            # Si es una factura de POS
            if move.pos_order_ids:
                pos_order = move.pos_order_ids[0]
                if pos_order.pricelist_id:
                    # Asegurar que ambos campos tengan el mismo valor
                    move.write({
                        'x_studio_lista_de_precio': pos_order.pricelist_id.id,
                        'x_studio_lista_de_precio_1': pos_order.pricelist_id.id,
                    })
        
        return moves