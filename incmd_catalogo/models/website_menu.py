# -*- coding: utf-8 -*-

from odoo import models


class WebsiteMenu(models.Model):
    _inherit = 'website.menu'

    def _compute_visible(self):
        """Oculta los menús públicos de los catálogos deshabilitados.

        El bloqueo real de acceso se realiza también en el controlador. Esta
        validación únicamente evita mostrar enlaces a catálogos desactivados.
        """
        super()._compute_visible()
        params = self.env['ir.config_parameter'].sudo()

        def _enabled(key):
            value = params.get_param('incmd_catalogo.%s.enabled' % key, 'True')
            return str(value).strip().lower() in ('1', 'true', 'yes', 'y', 'on', 'si', 'sí')

        incomel_enabled = _enabled('incomel')
        tecnialiado_enabled = _enabled('tecnialiado')

        for menu in self:
            url = (menu.url or '').strip()
            if url.startswith('/incomel') and not incomel_enabled:
                menu.is_visible = False
            elif url.startswith('/tecnialiado') and not tecnialiado_enabled:
                menu.is_visible = False
