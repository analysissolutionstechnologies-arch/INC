from markupsafe import Markup
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError

ADMIN = 'incmd_requests.group_admin'
ORIGINAL = {'name','description','requester_id','origin_id','unit_id','reason_id','original_attachment_ids','company_id'}
CONTROL = {'number','process_id','stage_id','state','submitted_at','closed_at','responsible_id'}

class Request(models.Model):
    _name = 'incmd.request'
    _description = 'Solicitud interna'
    _inherit = ['mail.thread','mail.activity.mixin']
    _order = 'create_date desc,id desc'
    _rec_name = 'number'
    number = fields.Char(default='Borrador',readonly=True,copy=False,string='Solicitud',index=True)
    name = fields.Char(required=True,tracking=True,string='Asunto')
    description = fields.Text(required=True,string='Descripción')
    company_id = fields.Many2one('res.company',required=True,default=lambda self:self.env.company,readonly=True)
    requester_id = fields.Many2one('res.users',required=True,default=lambda self:self.env.user,readonly=True,string='Solicitante')
    origin_id = fields.Many2one('incmd.request.unit',required=True,default=lambda self:self._default_origin(),readonly=True,string='Área o tienda de origen')
    unit_id = fields.Many2one('incmd.request.unit',required=True,ondelete='restrict',string='Área destinataria',domain="[('receives','=',True),('company_id','=',company_id)]")
    reason_id = fields.Many2one('incmd.request.reason',required=True,ondelete='restrict',string='Motivo',domain="[('unit_id','=',unit_id),('active','=',True)]")
    process_id = fields.Many2one('incmd.request.process',readonly=True,ondelete='restrict',copy=False,string='Proceso y versión')
    stage_id = fields.Many2one('incmd.request.stage',readonly=True,ondelete='restrict',tracking=True,copy=False,string='Etapa',group_expand='_expand_stages')
    state = fields.Selection([('draft','Borrador'),('open','En atención'),('done','Finalizada'),('rejected','Rechazada')],default='draft',required=True,readonly=True,copy=False,tracking=True,string='Estado')
    responsible_id = fields.Many2one('res.users',readonly=True,tracking=True,string='Responsable de seguimiento')
    submitted_at = fields.Datetime(readonly=True,string='Enviada el',copy=False)
    closed_at = fields.Datetime(readonly=True,string='Cerrada el',copy=False)
    original_attachment_ids = fields.Many2many('ir.attachment','incmd_request_original_rel','request_id','attachment_id',string='Adjuntos originales',copy=False)
    history_ids = fields.One2many('incmd.request.history','request_id',readonly=True,string='Historial')
    can_handle = fields.Boolean(compute='_compute_can_handle')
    is_owner = fields.Boolean(compute='_compute_can_handle')

    @api.model
    def _default_origin(self):
        direct = self.env['incmd.request.assignment'].search([
            ('user_id','=',self.env.uid),('company_id','=',self.env.company.id)],limit=1).unit_id
        if direct: return direct
        # Consulta interna acotada al empleado del usuario actual y compañía activa.
        # No se expone información de RR. HH. a los usuarios del módulo.
        employees = self.env['hr.employee'].sudo().search([
            ('user_id','=',self.env.uid),('company_id','=',self.env.company.id)],limit=2)
        if len(employees) != 1: return self.env['incmd.request.unit']
        employee = employees[0]
        unit = employee.request_unit_id
        if not unit and employee.department_id:
            unit = self.env['incmd.request.unit'].sudo().search([
                ('department_id','=',employee.department_id.id),('company_id','=',self.env.company.id)],limit=1)
        # Devolver el registro con el entorno original; no propagar sudo.
        return self.env['incmd.request.unit'].browse(unit.id) if unit and unit.active else self.env['incmd.request.unit']

    @api.depends_context('uid')
    @api.depends('stage_id','state','origin_id','unit_id')
    def _compute_can_handle(self):
        for r in self:
            r.can_handle = r.state == 'open' and r._may_handle()
            r.is_owner = r.requester_id == self.env.user

    def _may_handle(self):
        self.ensure_one()
        u = self.env.user
        if u.has_group(ADMIN): return True
        s = self.stage_id
        if s.actor_type == 'origin_supervisor':
            return u.has_group('incmd_requests.group_supervisor') and u in self.origin_id.supervisor_ids
        if s.actor_type == 'users': return u in s.actor_ids
        return u in self.unit_id.member_ids

    @api.model
    def _expand_stages(self, stages, domain):
        # Only expand one selected process; never mix unrelated columns automatically.
        pid = self.env.context.get('default_process_id')
        return self.env['incmd.request.stage'].search([('process_id','=',pid)]) if pid else stages

    @api.onchange('unit_id')
    def _onchange_unit(self):
        if self.reason_id.unit_id != self.unit_id: self.reason_id = False

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.user.has_group('incmd_requests.group_user'): raise AccessError(_('Sin permiso de solicitudes.'))
        origin = self._default_origin()
        if not origin: raise UserError(_('Configure su área o tienda desde Empleados o mediante una asignación directa en esta compañía.'))
        cleaned = []
        for vals in vals_list:
            v = dict(vals)
            if any(k in v for k in CONTROL) or v.get('requester_id',self.env.uid) != self.env.uid:
                raise AccessError(_('Los datos de control se asignan automáticamente.'))
            if v.get('origin_id',origin.id) != origin.id or v.get('company_id',self.env.company.id) != self.env.company.id:
                raise AccessError(_('No puede suplantar el origen de una solicitud.'))
            v.update(requester_id=self.env.uid,origin_id=origin.id,company_id=self.env.company.id)
            cleaned.append(v)
        return super().create(cleaned)

    def write(self, vals):
        if CONTROL.intersection(vals): raise AccessError(_('Utilice las acciones de seguimiento para cambiar el estado o responsable.'))
        if ORIGINAL.intersection(vals):
            for r in self:
                if r.state != 'draft': raise UserError(_('La solicitud enviada es inmutable, incluso para el administrador.'))
                if r.requester_id != self.env.user: raise AccessError(_('Solo el solicitante modifica su borrador.'))
            if {'requester_id','origin_id','company_id'}.intersection(vals): raise AccessError(_('El origen y solicitante son automáticos.'))
        return super().write(vals)

    def unlink(self):
        for r in self:
            if r.state != 'draft' or r.requester_id != self.env.user:
                raise AccessError(_('Solo puede eliminar sus propios borradores.'))
        return super().unlink()

    @api.constrains('unit_id','reason_id','origin_id','company_id','original_attachment_ids')
    def _check_consistency(self):
        for r in self:
            if r.unit_id.company_id != r.company_id or r.origin_id.company_id != r.company_id or r.reason_id.unit_id != r.unit_id:
                raise ValidationError(_('El motivo y las unidades deben corresponder al área y compañía.'))
            for a in r.original_attachment_ids:
                if a.res_model and a.res_model != r._name or a.res_model == r._name and a.res_id not in (0,r.id):
                    raise ValidationError(_('El adjunto ya pertenece a otro documento.'))
                if a.create_uid != r.requester_id:
                    raise ValidationError(_('Adjunte archivos cargados por el solicitante.'))

    def _lock(self):
        self.ensure_one()
        self.env.cr.execute('SELECT id FROM incmd_request WHERE id = %s FOR UPDATE', [self.id])
        self.invalidate_recordset()
        self.check_access('write')

    def action_submit(self):
        self.ensure_one()
        self._lock()
        if self.requester_id != self.env.user or self.state != 'draft': raise AccessError(_('Solo puede enviar su propio borrador.'))
        if not self.origin_id.active or not self.unit_id.active or not self.unit_id.receives or not self.reason_id.active:
            raise UserError(_('El área o motivo no está disponible.'))
        if not (self.name or '').strip() or not (self.description or '').strip(): raise UserError(_('Complete asunto y descripción.'))
        process = self.reason_id.process_id
        if process.state != 'published' or process.unit_id != self.unit_id: raise UserError(_('El motivo no tiene un proceso publicado válido.'))
        stage = process.stage_ids.filtered('is_initial')
        if len(stage) != 1: raise UserError(_('El proceso necesita una etapa inicial.'))
        self.original_attachment_ids.write({'res_model':self._name,'res_id':self.id})
        number = self.env['ir.sequence'].next_by_code('incmd.request')
        super().write({'number':number,'process_id':process.id,'stage_id':stage.id,'state':'open','submitted_at':fields.Datetime.now()})
        self._record_event('Solicitud enviada',False,stage,'Se envió la solicitud al área destinataria.')
        self.message_subscribe(partner_ids=(self.unit_id.member_ids | self.origin_id.supervisor_ids).partner_id.ids)
        return True

    def action_process_board(self):
        self.ensure_one()
        self.check_access('read')
        if not self.process_id: raise UserError(_('Primero envíe la solicitud.'))
        return {'type':'ir.actions.act_window','name':self.process_id.display_name,
                'res_model':self._name,'view_mode':'kanban,list,form',
                'domain':[('process_id','=',self.process_id.id)],
                'context':dict(self.env.context,default_process_id=self.process_id.id)}

    def action_followup(self):
        self.ensure_one()
        self.check_access('read')
        if self.state != 'open': raise UserError(_('La solicitud ya está cerrada o todavía es borrador.'))
        return {'type':'ir.actions.act_window','res_model':'incmd.request.action','view_mode':'form','target':'new',
                'context':dict(self.env.context,default_request_id=self.id)}

    def _record_event(self, action, old, new, comment, attachments=None):
        self.ensure_one()
        self.env['incmd.request.history'].sudo().create({'request_id':self.id,'user_id':self.env.uid,
            'action':action,'from_stage_id':old.id if old else False,'to_stage_id':new.id if new else False,
            'comment':comment,'attachment_ids':[(6,0,attachments.ids)] if attachments else []})
        body = Markup('<strong>%s</strong><br/>%s') % (action,comment or '')
        self.message_post(body=body,attachment_ids=attachments.ids if attachments else [],subtype_xmlid='mail.mt_comment')

    def _apply_followup(self, transition, comment, attachments, responsible):
        self.ensure_one()
        self._lock()
        if self.state != 'open': raise UserError(_('La solicitud no está en atención.'))
        can_handle = self._may_handle()
        if not can_handle and self.requester_id != self.env.user: raise AccessError(_('Solo el solicitante o un responsable autorizado registra gestiones.'))
        if not (comment or '').strip(): raise UserError(_('Ingrese el comentario de seguimiento.'))
        for a in attachments:
            if a.create_uid != self.env.user or a.res_model and (a.res_model != 'incmd.request' or a.res_id not in (0,self.id)):
                raise AccessError(_('Adjunto no permitido.'))
        attachments.write({'res_model':self._name,'res_id':self.id})
        old = self.stage_id
        vals = {}
        action = 'Seguimiento registrado'
        if responsible:
            if not can_handle: raise AccessError(_('No puede asignar responsables.'))
            if responsible not in self.unit_id.member_ids: raise ValidationError(_('El responsable debe pertenecer al equipo destinatario.'))
            vals['responsible_id'] = responsible.id
        if transition:
            if not can_handle: raise AccessError(_('No puede cambiar la etapa.'))
            if transition.process_id != self.process_id or transition.from_stage_id != old:
                raise ValidationError(_('La acción no corresponde a la etapa o versión actual.'))
            if old.attachment_required and not attachments: raise UserError(_('Esta etapa exige un nuevo adjunto de evidencia.'))
            if old.requires_approval and transition.kind == 'advance': raise UserError(_('Esta etapa requiere aprobación explícita.'))
            vals['stage_id'] = transition.to_stage_id.id
            if transition.to_stage_id.is_closed:
                vals.update(state='rejected' if transition.kind == 'reject' else 'done',closed_at=fields.Datetime.now())
            action = transition.name
        if vals: super().write(vals)
        self._record_event(action,old,self.stage_id,comment,attachments)
        return True

class History(models.Model):
    _name = 'incmd.request.history'
    _description = 'Historial inmutable de solicitud'
    _order = 'create_date desc,id desc'
    request_id = fields.Many2one('incmd.request',required=True,ondelete='cascade')
    company_id = fields.Many2one(related='request_id.company_id',store=True)
    user_id = fields.Many2one('res.users',required=True,string='Usuario')
    action = fields.Char(required=True,string='Acción')
    from_stage_id = fields.Many2one('incmd.request.stage',string='Etapa anterior')
    to_stage_id = fields.Many2one('incmd.request.stage',string='Nueva etapa')
    comment = fields.Text(string='Comentario')
    attachment_ids = fields.Many2many('ir.attachment',string='Evidencia')
    def write(self, vals): raise AccessError(_('El historial no se modifica.'))
    def unlink(self): raise AccessError(_('El historial no se elimina.'))
