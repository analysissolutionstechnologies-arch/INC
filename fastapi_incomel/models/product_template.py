# # -*- coding: utf-8 -*-
#
# from odoo import fields, models, api
#
# class ProductTemplate(models.Model):
#     _inherit = 'product.template'
#
#     x_studio_marca = fields.Char(string='Marca')
#     x_studio_modelo = fields.Char(string='Modelo')
#
#
#     full_category_path = fields.Char(
#         string='Full Category Path',
#         compute='_compute_full_category_path',
#         store=True
#     )
#
#     @api.depends('categ_id')
#     def _compute_full_category_path(self):
#         for product in self:
#             if product.categ_id:
#                 product.full_category_path = self._get_full_category_path(product.categ_id)
#             else:
#                 product.full_category_path = False
#
#     def _get_full_category_path(self, category):
#         if category.parent_id:
#             return f"{self._get_full_category_path(category.parent_id)} / {category.name}"
#         else:
#             return category.name

# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_studio_marca = fields.Char(string='Marca')
    x_studio_modelo = fields.Char(string='Modelo')

    full_category_path = fields.Char(
        string='Full Category Path',
        compute='_compute_full_category_path',
        store=True
    )

    @api.depends('categ_id')
    def _compute_full_category_path(self):
        """
        Calcula la ruta completa de categorías para el producto.
        """
        for product in self:
            product.full_category_path = (
                self._get_full_category_path(product.categ_id) if product.categ_id else False
            )

    def _get_full_category_path(self, category):
        """
        Retorna la ruta completa de una categoría, desde la raíz hasta la categoría actual.
        """
        categories = []
        current_category = category
        while current_category:
            categories.append(current_category.name)
            current_category = current_category.parent_id
        return " / ".join(reversed(categories))
