# -*- coding: utf-8 -*-

from odoo import models


class PosSession(models.Model):
    _inherit = "pos.session"

    def _loader_params_product_product(self):
        result = super()._loader_params_product_product()
        fields = result.get("search_params", {}).get("fields", [])
        if "x_studio_es_moto_1" not in fields:
            fields.append("x_studio_es_moto_1")
        return result
