# -*- coding: utf-8 -*-
from odoo import models

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def _get_inventory_move_values(self, qty, location_id, location_dest_id, *args, **kwargs):
        """
        Heredamos la función que arma los valores del movimiento de inventario generado
        por un ajuste. Si en el contexto viene 'ajuste_tipo', sustituimos
        location_dest_id por la ubicación configurada para ese tipo.

        Leemos parámetros del sistema para obtener las ubicaciones a usar:
         - inventory_adjustment_location_id
         - inventory_consignment_adjustment_location_id

        Si los parámetros no existen, usamos los valores por defecto 14 y 1720.
        """
        values = super(StockQuant, self)._get_inventory_move_values(qty, location_id, location_dest_id, *args, **kwargs)

        tipo = self.env.context.get('ajuste_tipo')
        if not tipo:
            return values

        # Obtener ids desde parámetros del sistema (editable en Parámetros del sistema)
        params = self.env['ir.config_parameter'].sudo()
        try:
            loc_normal = int(params.get_param('inventory_adjustment_location_id', default=14))
        except Exception:
            loc_normal = 14
        try:
            loc_consignment = int(params.get_param('inventory_consignment_adjustment_location_id', default=1720))
        except Exception:
            loc_consignment = 1720

        if tipo == 'consignacion':
            values['location_dest_id'] = loc_consignment
        else:
            values['location_dest_id'] = loc_normal

        return values