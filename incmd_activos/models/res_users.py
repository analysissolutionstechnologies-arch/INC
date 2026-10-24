# -*- coding: utf-8 -*-
import hashlib

from odoo import fields, models, _
from odoo.exceptions import UserError


class ResUsers(models.Model):
    _inherit = 'res.users'

    incmd_activos_auth_password_hash = fields.Char(
        string='Contraseña de autorización de activos',
        copy=False,
        readonly=True,
        groups='base.group_user',
    )

    def _incmd_activos_hash_password(self, password):
        self.ensure_one()
        password = (password or '').strip()
        return hashlib.sha256(('%s:%s' % (self.id, password)).encode('utf-8')).hexdigest()

    def _incmd_activos_set_auth_password(self, password):
        self.ensure_one()
        password = (password or '').strip()
        if not password:
            raise UserError(_('La contraseña de autorización no puede estar en blanco.'))
        self.sudo().write({
            'incmd_activos_auth_password_hash': self._incmd_activos_hash_password(password)
        })
        return True

    def _incmd_activos_check_auth_password(self, password):
        self.ensure_one()
        password = (password or '').strip()
        if not self.sudo().incmd_activos_auth_password_hash:
            raise UserError(_('Debe configurar su contraseña de autorización antes de continuar.'))
        if not password or self.sudo().incmd_activos_auth_password_hash != self._incmd_activos_hash_password(password):
            raise UserError(_('Contraseña de autorización incorrecta.'))
        return True
