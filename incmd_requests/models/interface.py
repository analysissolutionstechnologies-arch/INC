"""Datos para la interfaz Owl. Todas las operaciones conservan ACL y reglas ORM."""
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError

CARD_FIELDS = ['number','name','origin_id','unit_id','reason_id','process_id','stage_id',
               'requester_id','responsible_id','state','create_date','submitted_at','closed_at']
CONFIG = {
    'units': ('incmd.request.unit', ['name','kind','receives','active','department_id','member_ids','supervisor_ids']),
    'assignments': ('incmd.request.assignment', ['user_id','unit_id','role']),
    'reasons': ('incmd.request.reason', ['name','unit_id','process_id','description','active']),
    'processes': ('incmd.request.process', ['name','unit_id','version']),
    'stages': ('incmd.request.stage', ['name','sequence','process_id','is_initial','is_closed','requires_approval','attachment_required','actor_type','actor_ids']),
    'transitions': ('incmd.request.transition', ['name','sequence','process_id','from_stage_id','to_stage_id','kind']),
}

class RequestInterface(models.Model):
    _inherit = 'incmd.request'

    @api.model
    def _ui_guard(self, admin=False):
        group = 'incmd_requests.group_admin' if admin else 'incmd_requests.group_user'
        if not self.env.user.has_group(group): raise AccessError(_('No tiene permiso para esta pantalla.'))

    @api.model
    def ui_bootstrap(self):
        self._ui_guard()
        company = self.env.company
        origin = self._default_origin()
        area_domain = [('company_id','=',company.id)]
        return {
            'uid':self.env.uid,'user_name':self.env.user.name,'company':[company.id,company.name],
            'origin':[origin.id,origin.name] if origin else False,
            'admin':self.env.user.has_group('incmd_requests.group_admin'),
            'supervisor':self.env.user.has_group('incmd_requests.group_supervisor'),
            'units':self.env['incmd.request.unit'].search_read(area_domain,['name','kind','receives'],order='name'),
            'reasons':self.env['incmd.request.reason'].search_read(area_domain,['name','unit_id','process_id','description'],order='name'),
            'processes':self.env['incmd.request.process'].search_read(area_domain,[
                'name','display_title','unit_id','version','state'],order='name,version desc'),
        }

    @api.model
    def _ui_domain(self, options):
        self._ui_guard()
        domain = [('company_id','=',self.env.company.id)]
        mode = options.get('mode','mine')
        if mode == 'mine': domain.append(('requester_id','=',self.env.uid))
        elif mode == 'supervision':
            if not self.env.user.has_group('incmd_requests.group_supervisor'):
                raise AccessError(_('Se requiere perfil Supervisor.'))
            domain += [('state','!=','draft'),('origin_id.supervisor_ids','in',[self.env.uid])]
        elif mode == 'inbox':
            domain.append(('state','!=','draft'))
            if not self.env.user.has_group('incmd_requests.group_admin'):
                domain = ['|',('unit_id.member_ids','in',[self.env.uid]),('stage_id.actor_ids','in',[self.env.uid])] + domain
        else: raise ValidationError(_('Vista no permitida.'))
        if options.get('status') in ('draft','open','done','rejected'):
            domain.append(('state','=',options['status']))
        for key in ('origin_id','unit_id','process_id'):
            if options.get(key): domain.append((key,'=',int(options[key])))
        query = str(options.get('query','')).strip()[:200]
        if query:
            domain = ['|',('number','ilike',query),('name','ilike',query)] + domain
        return domain

    @api.model
    def ui_list(self, options=None):
        options = options or {}
        domain = self._ui_domain(options)
        offset = max(0,int(options.get('offset',0)))
        return {'records':self.search_read(domain,CARD_FIELDS,limit=40,offset=offset),
                'total':self.search_count(domain)}

    @api.model
    def ui_board(self, process_id, options=None):
        options = dict(options or {},process_id=int(process_id))
        domain = self._ui_domain(options)
        domain.append(('state','!=','draft'))
        process = self.env['incmd.request.process'].browse(int(process_id))
        process.check_access('read')
        if process.company_id != self.env.company: raise AccessError(_('Compañía no permitida.'))
        columns = []
        for stage in process.stage_ids:
            stage_domain = domain + [('stage_id','=',stage.id)]
            columns.append({'id':stage.id,'name':stage.name,'closed':stage.is_closed,
                'cards':self.search_read(stage_domain,CARD_FIELDS,limit=30),
                'total':self.search_count(stage_domain)})
        return {'columns':columns,'name':process.display_name}

    def ui_detail(self):
        self.ensure_one()
        self._ui_guard()
        self.check_access('read')
        data = self.read(CARD_FIELDS + ['original_unit_id','original_reason_id','description','can_handle','is_owner','original_attachment_ids'])[0]
        data['stages'] = self.process_id.stage_ids.read(['name','sequence','is_closed']) if self.process_id else []
        data['transitions'] = self.env['incmd.request.transition'].search_read([
            ('process_id','=',self.process_id.id),('from_stage_id','=',self.stage_id.id)],
            ['name','kind','to_stage_id'],order='sequence,id') if self.can_handle else []
        data['team'] = self.unit_id.member_ids.read(['name']) if self.can_handle else []
        data['attachment_required'] = bool(self.stage_id.attachment_required)
        data['approval'] = bool(self.stage_id.requires_approval)
        history = self.history_ids.read(['user_id','action','comment','create_date','from_stage_id','to_stage_id','attachment_ids','message_id'])
        message_ids = [h['message_id'][0] for h in history if h.get('message_id')]
        data['history'] = history
        data['messages'] = self.env['mail.message'].search_read([
            ('model','=',self._name),('res_id','=',self.id),('message_type','=','comment'),('id','not in',message_ids)],
            ['author_id','body','date','attachment_ids'],order='date desc,id desc',limit=200)
        attachment_ids = set(self.original_attachment_ids.ids)
        for item in history + data['messages']: attachment_ids.update(item['attachment_ids'])
        data['attachments'] = self.env['ir.attachment'].browse(sorted(attachment_ids)).read(['name','file_size','mimetype'])
        return data

    @api.model
    def ui_configuration(self):
        self._ui_guard(admin=True)
        domain = [('company_id','=',self.env.company.id)]
        result = {}
        for key,(model,fields_) in CONFIG.items():
            extras = {'processes':['state','stage_ids','transition_ids','display_title']}.get(key,[])
            result[key] = self.env[model].with_context(active_test=False).search_read(domain,fields_+extras,order='id')
        result['users'] = self.env['res.users'].search_read([
            ('share','=',False),('company_ids','in',[self.env.company.id])],['name'],order='name')
        result['departments'] = self.env['hr.department'].search_read([
            '|',('company_id','=',False),('company_id','=',self.env.company.id)],['name'],order='name')
        return result

    @api.model
    def ui_save_configuration(self, kind, record_id, values):
        self._ui_guard(admin=True)
        if kind not in CONFIG: raise ValidationError(_('Configuración no permitida.'))
        model,allowed = CONFIG[kind]
        if set(values) - set(allowed): raise ValidationError(_('Campos de configuración no permitidos.'))
        record = self.env[model].browse(int(record_id or 0))
        if record:
            record.check_access('write')
            if record.company_id != self.env.company: raise AccessError(_('Compañía no permitida.'))
            record.write(values)
        else:
            record = self.env[model].create(values)
            if record.company_id != self.env.company: raise AccessError(_('Compañía no permitida.'))
        return record.id

    @api.model
    def ui_delete_configuration(self, kind, record_id):
        self._ui_guard(admin=True)
        if kind not in CONFIG: raise ValidationError(_('Configuración no permitida.'))
        record = self.env[CONFIG[kind][0]].browse(int(record_id))
        record.check_access('unlink')
        if record.company_id != self.env.company: raise AccessError(_('Compañía no permitida.'))
        record.unlink()
        return True
