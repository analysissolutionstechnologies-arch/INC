# -*- coding: utf-8 -*-
from odoo import api, models


class AccountMoveIncomel(models.Model):
    """
    Extiende account.move para:
    - Buscar por NIT del proveedor además del número de factura.
    - Mostrar solo el número de factura en el campo Many2one (sin nombre del partner).
    """
    _inherit = 'account.move'

    @api.model
    def _name_search(self, name='', domain=None, operator='ilike', limit=100, order=None):
        domain = domain or []
        if name:
            domain = [
                '|', '|',
                ('name', operator, name),
                ('partner_id.name', operator, name),
                ('partner_id.vat', operator, name),
            ] + domain
        return super()._name_search(
            name='', domain=domain, operator=operator, limit=limit, order=order
        )

    def name_get(self):
        """Mostrar solo el número de factura, sin datos del proveedor."""
        result = []
        for move in self:
            result.append((move.id, move.name or '/'))
        return result
