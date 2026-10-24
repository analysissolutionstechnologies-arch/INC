# -*- coding: utf-8 -*-
from odoo import api, models


class ProductTemplateBarcode(models.Model):
    """
    Extiende product.template únicamente para la pantalla de activos.

    IMPORTANTE:
    - No se aplica filtro global de detailed_type.
    - El filtro de artículos se mantiene en la vista incmd.activo con domain.
    - La búsqueda por código de barras solo se activa cuando el contexto
      trae search_by_barcode=True desde la pantalla de activos.
    """
    _inherit = 'product.template'

    @api.model
    def _name_search(self, name='', domain=None, operator='ilike', limit=100, order=None):
        domain = list(domain or [])

        # Solo alterar la búsqueda cuando viene desde el campo product_id
        # del módulo de activos fijos.
        if self.env.context.get('search_by_barcode') and name:
            domain = ['|', ('barcode', operator, name), ('name', operator, name)] + domain
            return super()._name_search(
                name='', domain=domain, operator=operator, limit=limit, order=order
            )

        return super()._name_search(
            name=name, domain=domain, operator=operator, limit=limit, order=order
        )
