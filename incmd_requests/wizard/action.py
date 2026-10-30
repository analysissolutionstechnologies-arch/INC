from odoo import fields, models, _
from odoo.exceptions import AccessError

class Followup(models.TransientModel):
    _name = 'incmd.request.action'
    _description = 'Registrar seguimiento o ejecutar acción'
    request_id = fields.Many2one('incmd.request',required=True,readonly=True,string='Solicitud')
    stage_id = fields.Many2one(related='request_id.stage_id')
    can_handle = fields.Boolean(related='request_id.can_handle')
    transition_id = fields.Many2one('incmd.request.transition',string='Acción de etapa',domain="[('from_stage_id','=',stage_id)]",help='Vacío: registrar comentario sin cambiar de etapa.')
    comment = fields.Text(required=True,string='Comentario')
    attachment_ids = fields.Many2many('ir.attachment',string='Nuevos adjuntos')
    responsible_id = fields.Many2one('res.users',string='Asignar responsable',domain=[('share','=',False)])
    def action_apply(self):
        self.ensure_one()
        self.request_id.check_access('read')
        if self.create_uid != self.env.user: raise AccessError(_('El asistente pertenece a otro usuario.'))
        self.request_id._apply_followup(self.transition_id,self.comment,self.attachment_ids,self.responsible_id)
        return {'type':'ir.actions.act_window_close'}
