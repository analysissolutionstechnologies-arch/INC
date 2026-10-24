# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import UserError


class IncmdActivoHistory(models.Model):
    _name = 'incmd.activo.history'
    _description = 'Historial de Línea de Vida del Activo'
    _order = 'date desc, id desc'

    activo_id = fields.Many2one('incmd.activo', string='Activo', required=True, ondelete='cascade', index=True)
    date = fields.Datetime(string='Fecha', required=True, default=fields.Datetime.now, readonly=True)
    origin_location_id = fields.Many2one('stock.warehouse', string='Ubicación Origen', readonly=True)
    destination_location_id = fields.Many2one('stock.warehouse', string='Ubicación Destino', readonly=True)
    department_id = fields.Many2one('hr.department', string='Departamento', readonly=True)
    responsible_employee_id = fields.Many2one('hr.employee', string='Persona Responsable', readonly=True)
    event_type = fields.Selection([
        ('alta', 'Alta'),
        ('traslado', 'Traslado'),
        ('baja', 'Baja'),
        ('cambio_estado', 'Cambio de Estado'),
    ], string='Tipo de Evento', required=True, readonly=True)
    executed_by_id = fields.Many2one('res.users', string='Usuario que lo ejecutó', required=True, readonly=True)
    observation = fields.Text(string='Observación', readonly=True)

    def write(self, vals):
        raise UserError(_('No se permite modificar registros históricos de activos.'))

    def unlink(self):
        raise UserError(_('No se permite eliminar registros históricos de activos.'))
