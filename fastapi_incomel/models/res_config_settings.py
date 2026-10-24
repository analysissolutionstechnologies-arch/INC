# # -*- coding: utf-8 -*-
#
# import secrets
#
# from odoo import models, fields, api, tools
#
#
# class ResConfigSettings(models.TransientModel):
#     _inherit = "res.config.settings"
#
#     @api.model
#     @tools.ormcache()
#     def get_param_token(self):
#         return {
#             "secret_token": self.env["ir.config_parameter"].get_param(
#                 "fastapi.secret_token", False
#             ),
#             "refresh_secret_token": self.env["ir.config_parameter"].get_param(
#                 "fastapi.refresh_secret_token", False
#             ),
#             "access_token_expire_mitutes": self.env["ir.config_parameter"].get_param(
#                 "fastapi.access_token_expire_mitutes", 60
#             ),
#             "refresh_token_expire_days": self.env["ir.config_parameter"].get_param(
#                 "fastapi.refresh_token_expire_days", 90
#             ),
#         }
#
#     @api.model
#     def generator_fastapi_params(self):
#         self.env["ir.config_parameter"].set_param(
#             "fastapi.secret_token", secrets.token_hex(32)
#         )
#
#         self.env["ir.config_parameter"].set_param(
#             "fastapi.refresh_secret_token", secrets.token_hex(32)
#         )
#
#         self.env["ir.config_parameter"].set_param(
#             "fastapi.access_token_expire_mitutes", 60
#         )
#         self.env["ir.config_parameter"].set_param(
#             "fastapi.refresh_token_expire_days", 90
#         )

# -*- coding: utf-8 -*-

import secrets
from odoo import models, api, tools


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    @api.model
    @tools.ormcache()
    def get_param_token(self):
        """
        Obtiene los parámetros de configuración relacionados con FastAPI.
        Los valores se almacenan en caché para mejorar el rendimiento.
        """
        config_param = self.env["ir.config_parameter"]
        return {
            "secret_token": config_param.get_param("fastapi.secret_token", False),
            "refresh_secret_token": config_param.get_param("fastapi.refresh_secret_token", False),
            "access_token_expire_mitutes": int(
                config_param.get_param("fastapi.access_token_expire_mitutes", 60)
            ),
            "refresh_token_expire_days": int(
                config_param.get_param("fastapi.refresh_token_expire_days", 90)
            ),
        }

    @api.model
    def generator_fastapi_params(self):
        """
        Genera y guarda parámetros por defecto para FastAPI en `ir.config_parameter`.
        Incluye claves secretas y tiempos de expiración de tokens.
        """
        config_param = self.env["ir.config_parameter"]

        # Generar tokens secretos
        config_param.set_param("fastapi.secret_token", secrets.token_hex(32))
        config_param.set_param("fastapi.refresh_secret_token", secrets.token_hex(32))

        # Establecer tiempos de expiración por defecto
        config_param.set_param("fastapi.access_token_expire_mitutes", 60)
        config_param.set_param("fastapi.refresh_token_expire_days", 90)
