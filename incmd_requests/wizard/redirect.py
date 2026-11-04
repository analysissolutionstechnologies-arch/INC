from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError

class Redirect(models.TransientModel):
    _name = 'incmd.request.redirect'
    _description = 'Redirigir solicitud a otra área'
    request_id = fields.Many2one('incmd.request', required=True, readonly=True)
    company_id = fields.Many2one(related='request_id.company_id')
    unit_id = fields.Many2one('incmd.request.unit', required=True, string='Nueva área', domain="[('company_id','=',company_id),('receives','=',True)]")
    reason_id = fields.Many2one('incmd.request.reason', required=True, string='Nuevo motivo', domain="[('unit_id','=',unit_id),('active','=',True)]")
    process_id = fields.Many2one(related='reason_id.process_id', string='Proceso destino')
    responsible_id = fields.Many2one('res.users', string='Nuevo responsable', domain="[('share','=',False)]")
    comment = fields.Text(required=True, string='Justificación')

    @api.onchange('unit_id')
    def _onchange_unit(self):
        self.reason_id = False
        self.responsible_id = False

    def action_apply(self):
        self.ensure_one()
        if self.create_uid != self.env.user: raise AccessError(_('El asistente pertenece a otro usuario.'))
        if self.reason_id.unit_id != self.unit_id: raise ValidationError(_('El motivo no pertenece al área destino.'))
        self.request_id._apply_redirect(self.reason_id,self.comment,self.responsible_id)
        return {'type':'ir.actions.act_window_close'}
