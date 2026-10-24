# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Campo original: se mantiene para no romper datos anteriores.
    x_mostrar_en_catalogo = fields.Boolean(
        string='Mostrar en Catálogo Público',
        default=False,
        help='Compatibilidad con versiones anteriores del catálogo.',
    )
    x_mostrar_en_incomel = fields.Boolean(
        string='Mostrar en Incomel',
        default=False,
        help='Si está activo, el producto será visible en /incomel/catalogo.',
    )
    x_mostrar_en_tecnialiado = fields.Boolean(
        string='Mostrar en Tecnialiado',
        default=False,
        help='Si está activo, el producto será visible en /tecnialiado/catalogo.',
    )
    x_disponible = fields.Boolean(
        string='Disponible',
        default=True,
        help='Controla la etiqueta visual de disponibilidad en el catálogo público.',
    )
