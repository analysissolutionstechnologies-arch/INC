# -*- coding: utf-8 -*-
from odoo import api, models


class ResPartnerIncomel(models.Model):
    """
    Extiende res.partner para buscar por NIT (vat) en el campo
    supplier_partner_id de incmd.activo.
    """
    _inherit = 'res.partner'

    @api.model
    def _name_search(self, name='', domain=None, operator='ilike', limit=100, order=None):
        domain = domain or []
        if name:
            domain = ['|', ('vat', operator, name), ('name', operator, name)] + domain
        return super()._name_search(
            name='', domain=domain, operator=operator, limit=limit, order=order
        )
