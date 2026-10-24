# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import AccessDenied, UserError


class IncmdActivoAuthWizard(models.TransientModel):
    _name = 'incmd.activo.auth.wizard'
    _description = 'Autorización para Alta/Baja de Activo'

    activo_id = fields.Many2one('incmd.activo', string='Activo', required=True)
    action_type = fields.Selection([
        ('activate', 'Alta'),
        ('archive', 'Baja'),
    ], string='Acción', required=True)
    login = fields.Char(string='Usuario', required=True)
    password = fields.Char(string='Contraseña', required=True)
    observation = fields.Text(string='Observación de baja')

    def _validate_odoo_credentials(self):
        """Valida usuario y contraseña contra los usuarios de Odoo.

        Se mantiene la validación dentro del wizard para reemplazar la
        contraseña fija anterior. Si las credenciales son correctas, devuelve
        el usuario autorizado.
        """
        self.ensure_one()
        login = (self.login or '').strip()
        password = self.password or ''

        if not login or not password:
            raise UserError(_('Debe ingresar usuario y contraseña.'))

        user = self.env['res.users'].sudo().search([
            ('login', '=', login),
            ('active', '=', True),
        ], limit=1)
        if not user:
            raise UserError(_('Usuario o contraseña incorrectos.'))

        validation_errors = []

        # Firma común en Odoo 14-17: _check_credentials(password, user_agent_env)
        try:
            user.with_user(user)._check_credentials(password, {'interactive': True})
            return user
        except TypeError as exc:
            validation_errors.append(exc)
        except AccessDenied:
            raise UserError(_('Usuario o contraseña incorrectos.'))

        # Fallback para instalaciones con firma antigua: _check_credentials(password)
        try:
            user.with_user(user)._check_credentials(password)
            return user
        except TypeError as exc:
            validation_errors.append(exc)
        except AccessDenied:
            raise UserError(_('Usuario o contraseña incorrectos.'))

        # Fallback para método authenticate con firma antigua.
        try:
            uid = self.env['res.users'].sudo().authenticate(
                self.env.cr.dbname,
                login,
                password,
                {'interactive': True},
            )
            if uid == user.id:
                return user
        except TypeError as exc:
            validation_errors.append(exc)
        except AccessDenied:
            raise UserError(_('Usuario o contraseña incorrectos.'))

        # Fallback para método authenticate con credential dict.
        try:
            uid = self.env['res.users'].sudo().authenticate(
                self.env.cr.dbname,
                {'login': login, 'password': password, 'type': 'password'},
                {'interactive': True},
            )
            if uid == user.id:
                return user
        except TypeError as exc:
            validation_errors.append(exc)
        except AccessDenied:
            raise UserError(_('Usuario o contraseña incorrectos.'))

        if validation_errors:
            raise UserError(_('No fue posible validar las credenciales con la versión actual de Odoo.'))

        raise UserError(_('Usuario o contraseña incorrectos.'))

    def action_confirm(self):
        self.ensure_one()
        activo = self.activo_id
        authorized_user = self._validate_odoo_credentials()
        activo = activo.with_context(authorized_user_id=authorized_user.id)

        if self.action_type == 'activate':
            activo._ensure_code()
            activo.write({'state': 'assigned'})
            activo.message_post(
                body=_('Alta autorizada por: %s (%s)') % (authorized_user.name, authorized_user.login)
            )
            return self.env.ref('incmd_activos.action_report_incmd_responsabilidad').report_action(activo)

        if self.action_type == 'archive':
            observation = (self.observation or '').strip()
            if not observation:
                raise UserError(_('Debe ingresar una observación para dar de baja el activo.'))

            activo = activo.with_context(baja_observation=observation)
            activo.write({'state': 'archived'})
            activo.message_post(
                body=_('Baja autorizada por: %s (%s)<br/>Observación: %s') % (authorized_user.name, authorized_user.login, observation)
            )
            return self.env.ref('incmd_activos.action_report_incmd_linea_vida').report_action(activo)

        return {'type': 'ir.actions.act_window_close'}
