from odoo import models, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        """
        Sobreescribimos button_validate() para eliminar transferencias internas
        y todas las generadas después de validarse si tienen cantidades en 0.
        """
        res = super().button_validate()  # Validar la transferencia normalmente

        # Capturar la transferencia validada y TODAS las generadas después
        all_pickings = self | self.move_ids.move_dest_ids.picking_id

        for picking in all_pickings:
            if not picking.exists():  # Verificar que aún exista
                continue

            # Aplicamos solo a transferencias internas
            if picking.picking_type_id.code != 'internal':
                continue

            moves = picking.move_ids
            # Verificar si todas las líneas de stock tienen cantidades en 0
            if all(move.product_uom_qty == 0 and move.quantity == 0 for move in moves):
                picking.sudo().unlink()  # Eliminar la transferencia si cumple la condición

        return res  # Retornar la validación normal
