from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError, UserError

ADMIN = 'incmd_requests.group_admin'

class Unit(models.Model):
    _name = 'incmd.request.unit'
    _description = 'Área o tienda'
    _order = 'name'
    name = fields.Char(required=True, string='Nombre')
    kind = fields.Selection([('area', 'Área'), ('store', 'Tienda')], required=True, default='area', string='Tipo')
    active = fields.Boolean(default=True)
    receives = fields.Boolean(string='Recibe solicitudes', default=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    department_id = fields.Many2one('hr.department', string='Departamento de Empleados', ondelete='restrict', help='Los empleados de este departamento pueden obtener automáticamente esta unidad de origen.')
    _unique_department = models.Constraint('unique(department_id, company_id)', 'El departamento ya está vinculado a otra unidad de esta compañía.')
    member_ids = fields.Many2many('res.users', 'incmd_unit_member_rel', string='Equipo de atención', domain=[('share','=',False)])
    supervisor_ids = fields.Many2many('res.users', 'incmd_unit_supervisor_rel', string='Supervisores', domain=[('share','=',False)])

    @api.constrains('department_id','company_id')
    def _check_department_company(self):
        for r in self:
            if r.department_id.company_id and r.department_id.company_id != r.company_id:
                raise ValidationError(_('El departamento debe pertenecer a la compañía de la unidad.'))

class Employee(models.Model):
    _inherit = 'hr.employee'
    request_unit_id = fields.Many2one('incmd.request.unit', string='Área o tienda para solicitudes',
        groups='incmd_requests.group_admin', ondelete='restrict',
        domain="[('company_id','=',company_id)]",
        help='Opcional. Si se deja vacío, se toma la unidad vinculada al departamento del empleado.')

    @api.constrains('request_unit_id','company_id')
    def _check_request_unit(self):
        for r in self:
            if r.request_unit_id and r.request_unit_id.company_id != r.company_id:
                raise ValidationError(_('El área o tienda de solicitudes debe ser de la compañía del empleado.'))

class Assignment(models.Model):
    _name = 'incmd.request.assignment'
    _description = 'Asignación de usuario a área o tienda'
    user_id = fields.Many2one('res.users', required=True, ondelete='cascade', domain=[('share','=',False)], string='Usuario')
    unit_id = fields.Many2one('incmd.request.unit', required=True, ondelete='restrict', string='Área o tienda')
    company_id = fields.Many2one(related='unit_id.company_id', store=True)
    role = fields.Selection([('user','Usuario'),('supervisor','Supervisor'),('admin','Administrador')], compute='_compute_role', inverse='_inverse_role', string='Perfil del módulo')

    @api.depends('user_id')
    def _compute_role(self):
        for r in self:
            u = r.user_id
            r.role = 'admin' if u.has_group(ADMIN) else 'supervisor' if u.has_group('incmd_requests.group_supervisor') else 'user'

    def _inverse_role(self):
        if not self.env.user.has_group(ADMIN): raise AccessError(_('Solo el administrador asigna perfiles.'))
        all_roles = self.env['res.groups'].browse([self.env.ref('incmd_requests.group_' + x).id for x in ('user','supervisor','admin')])
        for r in self:
            if r.user_id.share: raise ValidationError(_('Solo se admiten usuarios internos.'))
            target = self.env.ref('incmd_requests.group_' + r.role)
            r.user_id.sudo().write({'group_ids': [(3,g.id) for g in all_roles] + [(4,target.id)]})

    @api.constrains('user_id','unit_id')
    def _check_internal(self):
        for r in self:
            if r.user_id.share: raise ValidationError(_('Solo se admiten usuarios internos.'))
            if r.unit_id.company_id not in r.user_id.company_ids:
                raise ValidationError(_('El usuario no tiene acceso a la compañía del área o tienda.'))

    _unique_user = models.Constraint('unique(user_id, company_id)', 'El usuario ya tiene una unidad en esta compañía.')

class Reason(models.Model):
    _name = 'incmd.request.reason'
    _description = 'Motivo de solicitud'
    name = fields.Char(required=True, string='Nombre')
    active = fields.Boolean(default=True)
    unit_id = fields.Many2one('incmd.request.unit', required=True, ondelete='restrict', string='Área destinataria', domain=[('receives','=',True)])
    company_id = fields.Many2one(related='unit_id.company_id', store=True)
    process_id = fields.Many2one('incmd.request.process', required=True, ondelete='restrict', string='Proceso publicado', domain="[('unit_id','=',unit_id),('state','=','published')]")
    description = fields.Text(string='Descripción e instrucciones')

    @api.constrains('unit_id','process_id')
    def _check_process(self):
        for r in self:
            if r.process_id.unit_id != r.unit_id or r.process_id.state != 'published':
                raise ValidationError(_('Seleccione un proceso publicado del área destinataria.'))

class Process(models.Model):
    _name = 'incmd.request.process'
    _description = 'Versión de proceso de solicitudes'
    _rec_name = 'display_title'
    name = fields.Char(required=True, string='Nombre')
    display_title = fields.Char(compute='_title', store=True)
    version = fields.Integer(default=1, required=True, string='Versión')
    unit_id = fields.Many2one('incmd.request.unit', required=True, ondelete='restrict', string='Área', domain=[('receives','=',True)])
    company_id = fields.Many2one(related='unit_id.company_id', store=True)
    state = fields.Selection([('draft','Borrador'),('published','Publicado')], default='draft', required=True, copy=False, string='Estado')
    _unique_version = models.Constraint('unique(name, unit_id, version)', 'Ya existe esta versión del proceso en el área.')
    _positive_version = models.Constraint('CHECK(version > 0)', 'La versión debe ser mayor que cero.')
    stage_ids = fields.One2many('incmd.request.stage','process_id', string='Etapas', copy=True)
    transition_ids = fields.One2many('incmd.request.transition','process_id',string='Acciones permitidas',copy=True)

    @api.depends('name','version')
    def _title(self):
        for r in self: r.display_title = '%s · v%s' % (r.name or '', r.version)

    def write(self, vals):
        if any(r.state == 'published' for r in self):
            raise UserError(_('El proceso publicado es inmutable. Cree una nueva versión.'))
        if 'state' in vals:
            raise UserError(_('Utilice Publicar versión.'))
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        if any(v.get('state','draft') != 'draft' for v in vals_list):
            raise UserError(_('El proceso debe crearse como borrador.'))
        return super().create(vals_list)

    def unlink(self):
        if any(r.state == 'published' for r in self): raise UserError(_('No se elimina un proceso publicado.'))
        return super().unlink()

    def action_publish(self):
        if not self.env.user.has_group(ADMIN): raise AccessError(_('Solo el administrador puede publicar.'))
        for r in self:
            if r.state != 'draft': raise UserError(_('El proceso ya está publicado.'))
            stages = r.stage_ids
            if len(stages.filtered('is_initial')) != 1 or not stages.filtered('is_closed'):
                raise ValidationError(_('Defina una única etapa inicial y al menos una etapa de cierre.'))
            if stages.filtered(lambda s:s.is_initial and s.is_closed):
                raise ValidationError(_('La etapa inicial no puede ser de cierre.'))
            for s in stages.filtered(lambda s: not s.is_closed):
                if not r.transition_ids.filtered(lambda t:t.from_stage_id == s):
                    raise ValidationError(_('La etapa %s necesita una acción de salida.', s.name))
            # Toda etapa debe ser alcanzable desde la inicial.
            reached = set(stages.filtered('is_initial').ids)
            while True:
                more = {t.to_stage_id.id for t in r.transition_ids if t.from_stage_id.id in reached}
                if more.issubset(reached): break
                reached |= more
            if reached != set(stages.ids): raise ValidationError(_('Hay etapas inaccesibles desde la etapa inicial.'))
            can_close = set(stages.filtered('is_closed').ids)
            while True:
                more = {t.from_stage_id.id for t in r.transition_ids if t.to_stage_id.id in can_close}
                if more.issubset(can_close): break
                can_close |= more
            if can_close != set(stages.ids): raise ValidationError(_('Cada etapa debe tener una ruta posible hasta un cierre.'))
            super(Process, r).write({'state':'published'})
        return True

    def action_new_version(self):
        self.ensure_one()
        if not self.env.user.has_group(ADMIN): raise AccessError(_('Solo el administrador puede versionar.'))
        # Copiar etapas y remapear transiciones; no conservar referencias a la versión anterior.
        latest = self.search([('name','=',self.name),('unit_id','=',self.unit_id.id)],order='version desc',limit=1)
        new = self.copy({'version':latest.version + 1,'state':'draft','transition_ids':False,'stage_ids':False})
        mapping = {}
        for s in self.stage_ids: mapping[s.id] = s.copy({'process_id':new.id}).id
        for t in self.transition_ids:
            t.copy({'process_id':new.id,'from_stage_id':mapping[t.from_stage_id.id],'to_stage_id':mapping[t.to_stage_id.id]})
        return {'type':'ir.actions.act_window','res_model':self._name,'res_id':new.id,'view_mode':'form','target':'current'}

class Stage(models.Model):
    _name = 'incmd.request.stage'
    _description = 'Etapa de proceso'
    _order = 'sequence,id'
    name = fields.Char(required=True,string='Etapa')
    sequence = fields.Integer(default=10,string='Orden')
    process_id = fields.Many2one('incmd.request.process',required=True,ondelete='cascade',string='Proceso')
    company_id = fields.Many2one(related='process_id.company_id',store=True)
    is_initial = fields.Boolean(string='Inicial')
    is_closed = fields.Boolean(string='Cierre')
    fold = fields.Boolean(related='is_closed')
    requires_approval = fields.Boolean(string='Requiere aprobación')
    attachment_required = fields.Boolean(string='Adjunto obligatorio')
    actor_type = fields.Selection([('team','Equipo destinatario'),('origin_supervisor','Supervisor de origen'),('users','Usuarios específicos')], default='team',required=True,string='Atiende la etapa')
    actor_ids = fields.Many2many('res.users',string='Usuarios autorizados',domain=[('share','=',False)])

    def _editable(self):
        if any(r.process_id.state == 'published' for r in self): raise UserError(_('Las etapas publicadas no pueden modificarse.'))

    @api.model_create_multi
    def create(self, vals_list):
        for v in vals_list:
            if self.env['incmd.request.process'].browse(v.get('process_id')).state == 'published':
                raise UserError(_('El proceso ya está publicado.'))
        return super().create(vals_list)

    def write(self, vals):
        self._editable()
        if 'process_id' in vals and self.env['incmd.request.process'].browse(vals['process_id']).state == 'published':
            raise UserError(_('El proceso ya está publicado.'))
        return super().write(vals)

    def unlink(self):
        self._editable()
        return super().unlink()

    @api.constrains('actor_type','actor_ids')
    def _check_actors(self):
        for s in self:
            if s.actor_type == 'users' and not s.actor_ids: raise ValidationError(_('Seleccione usuarios autorizados.'))

class Transition(models.Model):
    _name = 'incmd.request.transition'
    _description = 'Acción de proceso'
    _order = 'sequence,id'
    name = fields.Char(required=True,string='Acción')
    sequence = fields.Integer(default=10,string='Orden')
    process_id = fields.Many2one('incmd.request.process',required=True,ondelete='cascade',string='Proceso')
    company_id = fields.Many2one(related='process_id.company_id',store=True)
    from_stage_id = fields.Many2one('incmd.request.stage',required=True,ondelete='cascade',string='Desde',domain="[('process_id','=',process_id)]")
    to_stage_id = fields.Many2one('incmd.request.stage',required=True,ondelete='cascade',string='Hacia',domain="[('process_id','=',process_id)]")
    kind = fields.Selection([('advance','Avanzar'),('approve','Aprobar'),('return','Devolver'),('reject','Rechazar')],default='advance',required=True,string='Tipo')

    @api.constrains('process_id','from_stage_id','to_stage_id','kind')
    def _check_stages(self):
        for t in self:
            if t.from_stage_id.process_id != t.process_id or t.to_stage_id.process_id != t.process_id:
                raise ValidationError(_('Las etapas deben pertenecer al mismo proceso.'))
            if t.from_stage_id == t.to_stage_id or t.from_stage_id.is_closed:
                raise ValidationError(_('Origen y destino deben diferir; no se sale de una etapa de cierre.'))
            if t.kind == 'reject' and not t.to_stage_id.is_closed:
                raise ValidationError(_('El rechazo debe terminar en una etapa de cierre.'))
            if t.from_stage_id.requires_approval and t.kind == 'advance':
                raise ValidationError(_('Una etapa de aprobación requiere Aprobar, Devolver o Rechazar.'))

    def _editable(self):
        if any(t.process_id.state == 'published' for t in self): raise UserError(_('Las acciones publicadas son inmutables.'))

    @api.model_create_multi
    def create(self, vals_list):
        for v in vals_list:
            if self.env['incmd.request.process'].browse(v.get('process_id')).state == 'published':
                raise UserError(_('El proceso ya está publicado.'))
        return super().create(vals_list)

    def write(self, vals):
        self._editable()
        if 'process_id' in vals and self.env['incmd.request.process'].browse(vals['process_id']).state == 'published':
            raise UserError(_('El proceso ya está publicado.'))
        return super().write(vals)

    def unlink(self):
        self._editable()
        return super().unlink()
