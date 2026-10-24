# -*- coding: utf-8 -*-
from odoo import models, fields

class StockInventoryAdjustmentName(models.TransientModel):
    _inherit = "stock.inventory.adjustment.name"

    ajuste_tipo = fields.Selection([
        ('normal', 'Ajuste Normal'),
        ('consignacion', 'Ajuste Consignación'),
    ], string='Tipo de ajuste', default='normal')

    def action_apply(self):
        """
        Pasamos la elección de ajuste en el contexto antes de ejecutar la acción original.
        De esta forma, durante la creación de movimientos se puede leer self.env.context.get('ajuste_tipo').
        """
        # Usamos with_context para que durante la ejecución de la super() exista la clave en el contexto.
        return super(StockInventoryAdjustmentName, self.with_context(ajuste_tipo=self.ajuste_tipo)).action_apply()