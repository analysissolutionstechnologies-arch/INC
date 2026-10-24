# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class IncmdActivoTrasladoWizard(models.TransientModel):
    _name = 'incmd.activo.traslado.wizard'
    _description = 'Asistente de Traslado de Activo'

    activo_id = fields.Many2one('incmd.activo', string='Activo', required=True)
    origin_location_id = fields.Many2one(
        'stock.warehouse',
        string='Ubicación Origen',
        readonly=True
    )
    destination_location_id = fields.Many2one(
        'stock.warehouse',
        string='Ubicación Destino',
        required=True,
    )
    department_id = fields.Many2one('hr.department', string='Departamento')
    responsible_employee_id = fields.Many2one('hr.employee', string='Persona Responsable')
    note = fields.Text(string='Observaciones')

    @api.onchange('activo_id')
    def _onchange_activo_id(self):
        for rec in self:
            if rec.activo_id:
                rec.origin_location_id = rec.activo_id.location_id
                rec.responsible_employee_id = rec.activo_id.responsible_employee_id
                rec.department_id = rec.activo_id.department_id

    @api.constrains('destination_location_id', 'department_id')
    def _check_department_required_for_matriz(self):
        for rec in self:
            if rec.destination_location_id:
                name = (rec.destination_location_id.name or '').lower()
                if 'matriz' in name and not rec.department_id:
                    raise ValidationError(_('El Departamento es obligatorio cuando la ubicación destino corresponde a Matriz.'))

    def action_confirm(self):
        self.ensure_one()
        activo = self.activo_id

        vals = {
            'location_id': self.destination_location_id.id,
            'department_id': self.department_id.id if self.department_id else False,
            'responsible_employee_id': self.responsible_employee_id.id if self.responsible_employee_id else False,
            'state': 'assigned',
        }
        activo.write(vals)
        return self.env.ref('incmd_activos.action_report_incmd_traslado').report_action(activo)
