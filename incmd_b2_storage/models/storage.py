import io
import zipfile
import fnmatch
import hashlib
import logging
import os
import re
import pytz
import time
import shutil
from datetime import timedelta, datetime
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from odoo.http import Stream
_logger = logging.getLogger(__name__)
PREFIX = 'b2v2://'

class Repository(models.Model):
    _name = 'incmd.b2.repository'
    _description = 'Repositorio Backblaze'
    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    endpoint = fields.Char(required=True, default='https://s3.us-east-005.backblazeb2.com')
    region = fields.Char(required=True, default='us-east-005')
    bucket = fields.Char(required=True)
    key_id = fields.Char(required=True, groups='base.group_system')
    application_key = fields.Char(required=True, groups='base.group_system')
    folder = fields.Char(default='attachments', string='Carpeta raíz')
    storage_environment = fields.Selection([('produccion', 'Producción'), ('qa', 'QA'),
        ('desarrollo', 'Desarrollo')], string='Ambiente', required=True, default='desarrollo',
        help='Configure un destino distinto por ambiente. Cambiarlo solo afecta nuevas transferencias.')
    batch_size = fields.Integer(default=20, required=True)
    max_mb = fields.Integer(default=50, required=True)
    migration_enabled = fields.Boolean(default=False)
    automatic_enabled = fields.Boolean(string='Ejecución automática', default=False)
    interval_number = fields.Integer(string='Frecuencia', default=15, required=True)
    interval_type = fields.Selection([('minutes', 'Minutos'), ('hours', 'Horas'), ('days', 'Días')], default='minutes', required=True)
    retry_minutes = fields.Integer(string='Espera entre reintentos (min)', default=15, required=True)
    max_attempts = fields.Integer(string='Máximo de intentos', default=0, help='0: sin límite. Incluye el primer intento. Cambie el límite o use Reiniciar pendientes para continuar.')
    upload_mode = fields.Selection([('immediate', 'Al cargar'), ('scheduled', 'En la tarea programada')], default='scheduled', required=True, string='Modo de envío')
    path_timezone = fields.Selection(selection='_timezone_options', default='America/Guatemala', required=True, string='Zona horaria de carpetas')
    cron_id = fields.Many2one('ir.cron', readonly=True, copy=False, ondelete='set null', string='Tarea del repositorio')
    batch_seconds = fields.Integer(string='Presupuesto de lote (segundos)', default=45, required=True, help='Se comprueba entre archivos; una transferencia iniciada puede excederlo.')
    batch_failure_limit = fields.Integer(string='Pausar lote tras fallos (-1: ilimitado)', default=-1, required=True, help='-1: nunca detener el lote por fallos. Si es positivo, finalizar solo la ejecución actual al alcanzar el límite; no desactiva la tarea.')
    retry_cron_id = fields.Many2one('ir.cron', readonly=True, copy=False, ondelete='set null', string='Tarea de reintentos')
    retry_enabled = fields.Boolean(string='Reintentos independientes', default=True)
    retry_hour = fields.Integer(string='Hora de reintentos (0-23)', default=7, required=True)
    retry_batch_size = fields.Integer(string='Archivos por lote de reintentos', default=20, required=True)
    retry_batch_seconds = fields.Integer(string='Tiempo máximo de reintentos (seg)', default=45, required=True)
    network_timeout = fields.Integer(string='Timeout de lectura de red (segundos)', default=10, required=True)
    night_only = fields.Boolean(string='Procesar cola solo en horario nocturno', default=True)
    night_start = fields.Integer(string='Hora inicial (0–23)', default=22, required=True)
    night_end = fields.Integer(string='Hora final (0–23)', default=6, required=True)
    rule_ids = fields.One2many('incmd.b2.rule', 'repository_id')
    contingency_enabled = fields.Boolean(string='Contingencia: detener transferencias', default=False,
        help='Conserva nuevas cargas locales y mantiene la lectura remota. No cancela operaciones ya iniciadas.')
    recovery_reserve_mib = fields.Integer(string='Reserva mínima libre del filestore (MiB)', default=1024, required=True)
    contingency_result = fields.Text(string='Último resultado de contingencia', readonly=True, copy=False)

    def _contingency_check_access(self):
        self.ensure_one()
        if not self.env.user.has_group('base.group_system'):
            raise UserError(_('Solo un administrador puede ejecutar la contingencia.'))
        self.check_access_rights('write')
        self.check_access_rule('write')

    def action_contingency_test(self):
        self._contingency_check_access()
        attachment = self.env['ir.attachment'].sudo().search([
            ('store_fname', '=like', PREFIX + str(self.id) + '/%')], limit=1)
        if not attachment:
            self.contingency_result = _('No hay archivos remotos registrados para comprobar.')
            return True
        try:
            data = attachment._file_read(attachment.store_fname)
            valid = len(data) == attachment.file_size and hashlib.sha1(data).hexdigest() == attachment.checksum
            self.contingency_result = _('Lectura e integridad correctas del adjunto %s.') % attachment.id if valid else _('La verificación de integridad falló.')
        except Exception as exc:
            self.contingency_result = _('Lectura remota fallida: %s') % type(exc).__name__
        return True

    def action_contingency_recover(self):
        self._contingency_check_access()
        if not self.contingency_enabled:
            raise UserError(_('Active la contingencia antes de recuperar archivos.'))
        self.env.cr.execute('SELECT pg_try_advisory_xact_lock(%s)', [192837463])
        if not self.env.cr.fetchone()[0]:
            raise UserError(_('Hay una transferencia en curso. Espere a que termine y reintente.'))
        Attachment = self.env['ir.attachment'].sudo()
        records = Attachment.search([('store_fname', '=like', PREFIX + str(self.id) + '/%')],
                                    order='id', limit=self.batch_size)
        deadline = time.monotonic() + self.batch_seconds
        recovered = 0
        detail = ''
        for attachment in records:
            if time.monotonic() >= deadline:
                break
            try:
                with self.env.cr.savepoint():
                    self.env.cr.execute('SELECT id FROM ir_attachment WHERE id=%s FOR UPDATE SKIP LOCKED', [attachment.id])
                    if not self.env.cr.fetchone():
                        continue
                    attachment.invalidate_recordset()
                    if not (attachment.store_fname or '').startswith(PREFIX + str(self.id) + '/'):
                        continue
                    free = shutil.disk_usage(Attachment._filestore()).free
                    if free < attachment.file_size + max(0, self.recovery_reserve_mib) * 1024 * 1024:
                        raise UserError(_('Espacio insuficiente para recuperar conservando la reserva local.'))
                    payload = attachment._file_read(attachment.store_fname)
                    if len(payload) != attachment.file_size or hashlib.sha1(payload).hexdigest() != attachment.checksum:
                        raise UserError(_('Integridad incorrecta; se conserva la referencia remota.'))
                    local = attachment._file_write(payload, attachment.checksum)
                    with open(attachment._full_path(local), 'rb') as physical:
                        if hashlib.sha1(physical.read()).hexdigest() != attachment.checksum:
                            raise UserError(_('Falló la verificación del archivo local.'))
                    attachment.with_context(b2_internal=True).write({
                        'store_fname': local, 'db_datas': False, 'b2_state': 'local',
                        'b2_repository_id': False, 'b2_rule_id': False, 'b2_next_try': False,
                        'b2_attempts': 0, 'b2_thumbnail_key': False, 'b2_thumbnail_checksum': False})
                    recovered += 1
            except Exception as exc:
                detail = _(' Detenido en adjunto %(id)s: %(error)s') % {'id': attachment.id, 'error': str(exc) if isinstance(exc, UserError) else type(exc).__name__}
                break
        self.contingency_result = _('Recuperados a local: %s. Los objetos remotos se conservan.') % recovered + detail
        return True

    remote_count = fields.Integer(string='En Backblaze', compute='_compute_monitor')
    pending_count = fields.Integer(string='Pendientes', compute='_compute_monitor')
    due_count = fields.Integer(string='Con fecha cumplida', compute='_compute_monitor')
    exhausted_count = fields.Integer(string='Intentos agotados', compute='_compute_monitor')
    remote_mib = fields.Float(string='Contenido remoto registrado (MiB)', compute='_compute_monitor')
    pending_mib = fields.Float(string='Contenido pendiente (MiB)', compute='_compute_monitor')
    done_24h = fields.Integer(string='Transferencias últimas 24 h', compute='_compute_monitor')
    errors_24h = fields.Integer(string='Fallos últimas 24 h', compute='_compute_monitor')
    cleanup_count = fields.Integer(string='Limpiezas sin confirmar', compute='_compute_monitor')
    last_transfer = fields.Datetime(string='Última transferencia', compute='_compute_monitor')
    cron_active = fields.Boolean(string='Tarea activa', related='cron_id.active')
    next_execution = fields.Datetime(string='Próxima ejecución', related='cron_id.nextcall')

    def _compute_monitor(self):
        # Local database aggregates only: never enumerate/download bucket objects.
        self.check_access_rights('read')
        self.check_access_rule('read')
        names = ['remote_count', 'pending_count', 'due_count', 'exhausted_count',
            'remote_mib', 'pending_mib', 'done_24h', 'errors_24h', 'cleanup_count']
        for repo in self:
            for name in names:
                repo[name] = 0
            repo.last_transfer = False
        ids = [repo.id for repo in self if isinstance(repo.id, int) and repo.id > 0]
        if not ids:
            return
        self.env['ir.attachment'].flush_model(['b2_repository_id', 'b2_state', 'b2_attempts', 'b2_next_try', 'file_size', 'store_fname'])
        self.env['incmd.b2.audit'].flush_model(['repository_id', 'state', 'create_date', 'local_released'])
        now = fields.Datetime.now()
        self.env.cr.execute("""
            SELECT a.b2_repository_id,
                count(*) FILTER (WHERE a.store_fname LIKE 'b2v2://%%'),
                count(*) FILTER (WHERE a.b2_state='pending' AND coalesce(a.store_fname,'') NOT LIKE 'b2v2://%%'),
                count(*) FILTER (WHERE a.b2_state='pending' AND coalesce(a.store_fname,'') NOT LIKE 'b2v2://%%'
                    AND (a.b2_next_try IS NULL OR a.b2_next_try <= %s)
                    AND (r.max_attempts=0 OR coalesce(a.b2_attempts,0)<r.max_attempts)),
                count(*) FILTER (WHERE a.b2_state='pending' AND r.max_attempts>0 AND a.b2_attempts>=r.max_attempts),
                coalesce(sum(a.file_size) FILTER (WHERE a.store_fname LIKE 'b2v2://%%'),0),
                coalesce(sum(a.file_size) FILTER (WHERE a.b2_state='pending'),0)
            FROM ir_attachment a JOIN incmd_b2_repository r ON r.id=a.b2_repository_id
            WHERE a.b2_repository_id=ANY(%s) GROUP BY a.b2_repository_id
        """, [now, ids])
        for ident, remote, pending, due, exhausted, rb, pb in self.env.cr.fetchall():
            repo = self.browse(ident)
            repo.remote_count, repo.pending_count = remote, pending
            repo.due_count, repo.exhausted_count = due, exhausted
            repo.remote_mib, repo.pending_mib = rb / 1048576.0, pb / 1048576.0
        self.env.cr.execute("""
            SELECT repository_id,
                count(*) FILTER (WHERE state='done' AND create_date >= %s),
                count(*) FILTER (WHERE state='error' AND create_date >= %s),
                count(*) FILTER (WHERE state='done' AND NOT coalesce(local_released,false)),
                max(create_date) FILTER (WHERE state='done')
            FROM incmd_b2_audit WHERE repository_id=ANY(%s) GROUP BY repository_id
        """, [now-timedelta(hours=24), now-timedelta(hours=24), ids])
        for ident, done, errors, cleanup, last in self.env.cr.fetchall():
            repo = self.browse(ident)
            repo.done_24h, repo.errors_24h, repo.cleanup_count = done, errors, cleanup
            repo.last_transfer = last

    def _monitor_action(self, model, name, domain):
        self.ensure_one()
        self.check_access_rights('read')
        self.check_access_rule('read')
        return {'type': 'ir.actions.act_window', 'name': name, 'res_model': model,
            'view_mode': 'tree,form', 'domain': domain, 'context': {'create': False}}

    def action_pending(self):
        return self._monitor_action('ir.attachment', _('Pendientes del repositorio'),
            [('b2_repository_id','=',self.id),('b2_state','=','pending')])

    def action_remote(self):
        return self._monitor_action('ir.attachment', _('Archivos en Backblaze'),
            [('b2_repository_id','=',self.id),('store_fname','like',PREFIX+'%')])

    def action_exhausted(self):
        domain = [('b2_repository_id','=',self.id),('b2_state','=','pending')]
        domain += [('b2_attempts','>=',self.max_attempts)] if self.max_attempts else [('id','=',0)]
        return self._monitor_action('ir.attachment', _('Intentos agotados'), domain)

    def action_audit(self):
        return self._monitor_action('incmd.b2.audit', _('Transferencias del repositorio'),
            [('repository_id','=',self.id)])

    def action_recent_errors(self):
        return self._monitor_action('incmd.b2.audit', _('Fallos de las últimas 24 horas'),
            [('repository_id','=',self.id),('state','=','error'),
             ('create_date','>=',fields.Datetime.now()-timedelta(hours=24))])

    def action_cleanup_pending(self):
        return self._monitor_action('incmd.b2.audit', _('Limpiezas sin confirmar'),
            [('repository_id','=',self.id),('state','=','done'),('local_released','=',False)])

    @api.model
    def _timezone_options(self):
        return [(z, z) for z in pytz.all_timezones]

    def _b2_in_window(self, now=None):
        self.ensure_one()
        if not self.night_only:
            return True
        now = now or fields.Datetime.now()
        if now.tzinfo is None:
            now = pytz.UTC.localize(now)
        hour = now.astimezone(pytz.timezone(self.path_timezone)).hour
        if self.night_start < self.night_end:
            return self.night_start <= hour < self.night_end
        return hour >= self.night_start or hour < self.night_end

    @api.constrains('night_start', 'night_end')
    def _check_night_hours(self):
        for repo in self:
            if not 0 <= repo.night_start <= 23 or not 0 <= repo.night_end <= 23 or repo.night_start == repo.night_end:
                raise ValidationError(_('Defina horas distintas entre 0 y 23 para el inicio y fin del horario.'))

    @api.constrains('active')
    def _check_global_repository(self):
        self.env['incmd.b2.rule']._check_global_destination()

    @api.constrains('endpoint', 'batch_size', 'max_mb', 'interval_number', 'retry_minutes', 'max_attempts', 'folder', 'batch_seconds', 'batch_failure_limit', 'network_timeout', 'retry_hour', 'retry_batch_size', 'retry_batch_seconds')
    def _validate(self):
        for r in self:
            if not r.endpoint.startswith('https://') or not 1 <= r.batch_size <= 200 or r.max_mb < 1 or r.interval_number < 1 or r.retry_minutes < 1 or r.max_attempts < 0 or not 5 <= r.batch_seconds <= 600 or not (r.batch_failure_limit == -1 or 1 <= r.batch_failure_limit <= 200) or not 0 <= r.retry_hour <= 23 or not 1 <= r.retry_batch_size <= 200 or not 5 <= r.retry_batch_seconds <= 600 or not 1 <= r.network_timeout <= 60:
                raise ValidationError(_('Use HTTPS, lotes de 1 a 200, valores positivos de tamaño/frecuencia/espera y máximo de intentos >= 0; lote 5–600 s, fallos -1 o 1–200, hora 0–23, lote de reintentos 1–200, timeout 1–60 s.'))

    def action_sync_cron(self):
        self.check_access_rights('write')
        self.check_access_rule('write')
        old = self.env.ref('incmd_b2_storage.cron_b2_sync', raise_if_not_found=False)
        if old:
            old.sudo().write({'active': False})
        for repo in self:
            vals = {'name': 'Backblaze: %s' % repo.name,
                'model_id': self.env['ir.model']._get_id('incmd.b2.repository'),
                'state': 'code', 'code': 'model.browse(%d).action_batch()' % repo.id,
                'user_id': SUPERUSER_ID, 'interval_number': repo.interval_number,
                'interval_type': repo.interval_type, 'numbercall': -1, 'doall': False,
                'active': bool(repo.active and repo.automatic_enabled)}
            if repo.cron_id:
                repo.cron_id.sudo().write(vals)
            else:
                cron = self.env['ir.cron'].sudo().create(vals)
                super(Repository, repo).write({'cron_id': cron.id})
            repo._b2_sync_retry_cron()
        return True

    def _b2_sync_retry_cron(self):
        for repo in self:
            # ir.cron.nextcall is stored in UTC, while the configured hour is local.
            tz = pytz.timezone(repo.path_timezone or 'America/Guatemala')
            now_local = fields.Datetime.now().replace(tzinfo=pytz.UTC).astimezone(tz)
            naive_local = datetime.combine(now_local.date(), datetime.min.time()).replace(hour=repo.retry_hour)
            when = tz.localize(naive_local)
            if when <= now_local:
                when = tz.localize(naive_local + timedelta(days=1))
            vals = {'name': 'Backblaze: reintentos %s' % repo.name,
                'model_id': self.env['ir.model']._get_id('incmd.b2.repository'),
                'state': 'code', 'code': 'model.browse(%d).action_retry_batch()' % repo.id,
                'user_id': SUPERUSER_ID, 'interval_number': 1, 'interval_type': 'days',
                'nextcall': when.astimezone(pytz.UTC).replace(tzinfo=None),
                'numbercall': -1, 'doall': False,
                'active': bool(repo.active and repo.automatic_enabled and repo.retry_enabled)}
            if repo.retry_cron_id:
                repo.retry_cron_id.sudo().write(vals)
            else:
                cron = self.env['ir.cron'].sudo().create(vals)
                models.Model.write(repo, {'retry_cron_id': cron.id})

    def action_retry_batch(self):
        self.check_access_rights('write')
        self.check_access_rule('write')
        self.env['ir.attachment']._b2_retry_batch(self.ids)
        return True

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.action_sync_cron()
        return records

    def action_restart_pending(self):
        self.check_access_rights('write')
        self.check_access_rule('write')
        pending = self.env['ir.attachment'].sudo().search([
            ('b2_state', '=', 'pending'), ('b2_repository_id', 'in', self.ids)])
        pending.with_context(b2_internal=True).write({'b2_attempts': 0,
            'b2_next_try': fields.Datetime.now()})
        return True

    def _client(self):
        self.ensure_one()
        import boto3
        from botocore.config import Config
        r = self.sudo()
        # Each request is freshly signed. No permanent download token or URL.
        return boto3.client('s3', endpoint_url=r.endpoint, region_name=r.region,
            aws_access_key_id=r.key_id, aws_secret_access_key=r.application_key,
            config=Config(signature_version='s3v4', connect_timeout=5, read_timeout=r.network_timeout,
                          retries={'total_max_attempts': 1, 'mode': 'standard'}))

    def _call(self, operation, **kwargs):
        from botocore.exceptions import ClientError
        for attempt in range(2):
            try:
                return getattr(self._client(), operation)(Bucket=self.sudo().bucket, **kwargs)
            except ClientError as exc:
                code = exc.response.get('Error', {}).get('Code', '')
                if attempt or code not in ('ExpiredToken', 'InvalidToken', 'RequestExpired'):
                    raise
        raise UserError(_('No fue posible autenticar la solicitud.'))

    def action_test(self):
        self.ensure_one()
        try:
            self._call('head_bucket')
        except Exception:
            raise UserError(_('No se pudo conectar. Revise endpoint, bucket, credenciales y permisos.'))
        return {'type': 'ir.actions.client', 'tag': 'display_notification',
                'params': {'title': _('Backblaze'), 'message': _('Conexión correcta.'), 'type': 'success'}}

    def write(self, vals):
        if {'bucket', 'endpoint', 'region'} & vals.keys():
            if self.env['ir.attachment'].sudo().search_count([('b2_repository_id', 'in', self.ids)]):
                raise UserError(_('Este repositorio tiene archivos. Cree otro para cambiar su destino.'))
        result = super().write(vals)
        if {'name', 'active', 'automatic_enabled', 'interval_number', 'interval_type', 'retry_enabled', 'retry_hour', 'path_timezone'} & vals.keys():
            self.action_sync_cron()
        return result

    def unlink(self):
        if self.env['ir.attachment'].sudo().search_count([('b2_repository_id', 'in', self.ids)]):
            raise UserError(_('No puede eliminar un repositorio con archivos relacionados.'))
        self.mapped('cron_id').sudo().unlink()
        self.mapped('retry_cron_id').sudo().unlink()
        return super().unlink()

    def action_batch(self):
        self.check_access_rights('write')
        self.check_access_rule('write')
        self.env['ir.attachment']._b2_batch(self.ids)
        return True

class DocumentType(models.Model):
    _name = 'incmd.b2.document.type'
    _description = 'Tipo de documento Backblaze'
    name = fields.Char(required=True)
    mime_types = fields.Char(required=True)
    extensions = fields.Char(required=True)

class Rule(models.Model):
    _name = 'incmd.b2.rule'
    _description = 'Regla de documentos Backblaze'
    _order = 'sequence, id'
    sequence = fields.Integer(default=10, string='Prioridad', help='Menor valor gana. Se compara entre todas las reglas activas; empate: ID de regla. Un adjunto tiene un único repositorio.')
    active = fields.Boolean(default=True)
    scope = fields.Selection([('individual', 'Por módulo / modelo'), ('global', 'Global: todos los módulos')], default='individual', required=True, string='Alcance')
    excluded_model_ids = fields.Many2many('ir.model', 'incmd_b2_rule_excluded_model_rel', 'rule_id', 'model_id', string='Modelos excluidos', help='Exclusiones de esta regla global. Una regla individual puede enviar estos modelos a otro repositorio.')
    excluded_module_ids = fields.Many2many('ir.module.module', 'incmd_b2_rule_excluded_module_rel', 'rule_id', 'module_id', string='Módulos excluidos', domain=[('state', '=', 'installed')], help='Excluye modelos declarados o extendidos por estos módulos. Para mayor precisión use Modelos excluidos.')
    include_product_images = fields.Boolean(string='Incluir imágenes principales de productos', default=False, help='Autoriza image_1920 de product.template e image_variant_1920 de product.product. No incluye otros campos automáticamente.')
    repository_id = fields.Many2one('incmd.b2.repository', required=True, ondelete='cascade')
    module_id = fields.Many2one('ir.module.module', domain=[('state', '=', 'installed')])
    model_id = fields.Many2one('ir.model', string='Modelo específico (opcional)', ondelete='cascade')
    document_type_ids = fields.Many2many('incmd.b2.document.type', string='Tipos de documento', help='Si selecciona tipos, reemplazan los filtros MIME/extensiones manuales. Vacío conserva los filtros anteriores.')
    mime_types = fields.Char(required=True, default='image/jpeg,image/png,application/pdf')
    extensions = fields.Char(default='jpg,jpeg,png,pdf')
    allow_extensionless = fields.Boolean(default=True, string='Permitir documentos sin extensión', help='Valida por MIME permitido los adjuntos sin extensión. Conserva las exclusiones técnicas y la autorización de campos binarios.')
    field_names = fields.Char(help='Campos binarios de negocio permitidos, separados por coma. Vacío: solo adjuntos sin campo.')
    cursor_id = fields.Integer(default=0, readonly=True)

    @api.constrains('model_id', 'module_id', 'scope')
    def _check_model(self):
        for r in self:
            if r.scope == 'global':
                continue
            if not r.model_id and not r.module_id:
                raise ValidationError(_('Seleccione un módulo o un modelo específico.'))
            if r.model_id and r.model_id.model.startswith(('ir.', 'web.', 'bus.', 'base.')):
                raise ValidationError(_('Los modelos técnicos no pueden enviarse a Backblaze.'))
            if r.module_id and r.model_id and r.module_id.name not in (r.model_id.modules or '').split(', '):
                names = [s.strip() for s in (r.model_id.modules or '').split(',')]
                if r.module_id.name not in names:
                    raise ValidationError(_('El modelo no pertenece al módulo seleccionado.'))

    @api.constrains('scope', 'active', 'repository_id')
    def _check_global_destination(self):
        self.env.cr.execute('SELECT pg_advisory_xact_lock(%s)', [192837462])
        rules = self.sudo().search([('scope','=','global'),('active','=',True),('repository_id.active','=',True)])
        if len(rules) > 1:
            raise ValidationError(_('Solo se permite una regla global activa. Configure todos sus tipos en esa regla.'))

    def write(self, vals):
        if {'model_id', 'mime_types', 'extensions', 'allow_extensionless', 'field_names', 'active', 'repository_id', 'sequence', 'module_id', 'document_type_ids', 'scope', 'include_product_images', 'excluded_model_ids', 'excluded_module_ids'} & vals.keys():
            vals = dict(vals, cursor_id=0)
        return super().write(vals)

    @api.constrains('mime_types')
    def _check_mime(self):
        for rule in self:
            for token in rule.mime_types.split(','):
                if not re.fullmatch(r'[a-zA-Z0-9!#$&^_.+*-]+/[a-zA-Z0-9!#$&^_.+*-]+', token.strip()):
                    raise ValidationError(_('Separe los MIME con comas: image/jpeg,image/png,application/pdf.'))

    def _target_models(self):
        self.ensure_one()
        if self.scope == 'global':
            excluded_models = set(self.excluded_model_ids.mapped('model'))
            excluded_modules = set(self.excluded_module_ids.mapped('name'))
            return [m.model for m in self.env['ir.model'].sudo().search([])
                if not m.model.startswith(('ir.', 'web.', 'bus.', 'base.', 'theme.'))
                and m.model not in excluded_models
                and not excluded_modules.intersection(v.strip() for v in (m.modules or '').split(','))]
        if self.model_id:
            return [self.model_id.model]
        if not self.module_id:
            return []
        candidates = self.env['ir.model'].sudo().search([('modules', 'ilike', self.module_id.name)])
        return [m.model for m in candidates
            if self.module_id.name in [v.strip() for v in (m.modules or '').split(',')]]

    def _document_filters(self):
        self.ensure_one()
        if not self.document_type_ids:
            return self.mime_types, self.extensions
        return (','.join(self.document_type_ids.mapped('mime_types')),
                ','.join(self.document_type_ids.mapped('extensions')))

    def action_preview(self):
        self.ensure_one()
        candidates = self.env['ir.attachment'].search([
            ('res_model', 'in', self._target_models()), ('type', '=', 'binary'),
            '|', ('store_fname', '=', False), ('store_fname', 'not like', PREFIX + '%')],
            order='id desc', limit=2000)
        matches = candidates.filtered(lambda a: a._b2_rule() == self
            and a.file_size <= self.repository_id.max_mb * 1024 * 1024
            and (a.b2_state != 'pending' or not a.b2_repository_id or a.b2_repository_id == self.repository_id))
        return {'type': 'ir.actions.act_window',
            'name': _('Coincidencias: hasta los últimos 2000 candidatos'),
            'res_model': 'ir.attachment', 'view_mode': 'tree,form',
            'domain': [('id', 'in', matches.ids)], 'context': {'create': False}}

    def action_reset(self):
        self.write({'cursor_id': 0})
        return True

class Audit(models.Model):
    _name = 'incmd.b2.audit'
    _description = 'Historial de transferencia Backblaze'
    _order = 'id desc'
    attachment_id = fields.Many2one('ir.attachment', ondelete='set null')
    attachment_number = fields.Integer()
    name = fields.Char()
    res_model = fields.Char()
    res_id = fields.Integer()
    res_field = fields.Char()
    repository_id = fields.Many2one('incmd.b2.repository', ondelete='restrict')
    old_location = fields.Char()
    remote_key = fields.Char()
    state = fields.Selection([('done','Transferido'),('error','Pendiente / error'),('skip','Omitido')])
    detail = fields.Char()
    local_released = fields.Boolean(readonly=True)
    cleanup_attempts = fields.Integer(string='Errores de limpieza', readonly=True, default=0)
    cleanup_next_try = fields.Datetime(string='Próximo reintento de limpieza', readonly=True)
    cleanup_error = fields.Char(string='Detalle de limpieza', readonly=True)

class Attachment(models.Model):
    _inherit = 'ir.attachment'
    b2_repository_id = fields.Many2one('incmd.b2.repository', ondelete='restrict', readonly=True, copy=False)
    b2_retry_queued = fields.Boolean(string='En cola de reintento', default=False, readonly=True, copy=False, index=True)
    b2_state = fields.Selection([('local','Local'),('pending','Pendiente'),('remote','Backblaze')], default='local', readonly=True, copy=False)
    b2_attempts = fields.Integer(string='Intentos fallidos', readonly=True, copy=False, default=0)
    b2_rule_id = fields.Many2one('incmd.b2.rule', readonly=True, copy=False, ondelete='set null')
    b2_next_try = fields.Datetime(readonly=True, copy=False)
    b2_thumbnail_key = fields.Char(string='Miniatura remota', readonly=True, copy=False)
    b2_thumbnail_checksum = fields.Char(readonly=True, copy=False)
    b2_thumbnail_attempts = fields.Integer(string='Intentos miniatura', readonly=True, copy=False, default=0)
    b2_thumbnail_next_try = fields.Datetime(readonly=True, copy=False)
    b2_thumbnail_error = fields.Char(string='Error miniatura', readonly=True, copy=False)


    b2_location = fields.Selection([
        ('cloud', '☁️ Backblaze'), ('local', '💾 Local'),
        ('pending', '⏳ Pendiente'), ('url', '🔗 Enlace'),
        ('external', '☁️ Otro repositorio'), ('database', '💾 BD / sin físico'),
    ], string='Almacenamiento', compute='_compute_b2_location', store=True, compute_sudo=True)
    b2_remote_key = fields.Char(string='Clave remota', compute='_compute_b2_remote_key', compute_sudo=False)
    b2_local_copy = fields.Boolean(string='Físico local presente', compute='_compute_b2_local_copy')
    b2_local_bytes = fields.Integer(string='Bytes físicos locales', compute='_compute_b2_local_copy')

    @api.depends('store_fname', 'type', 'b2_state')
    def _compute_b2_location(self):
        for a in self:
            fname = a.store_fname or ''
            if fname.startswith(PREFIX):
                a.b2_location = 'cloud'
            elif a.type == 'url':
                a.b2_location = 'url'
            elif '://' in fname:
                a.b2_location = 'external'
            elif a.b2_state == 'pending':
                a.b2_location = 'pending'
            elif fname:
                a.b2_location = 'local'
            else:
                a.b2_location = 'database'

    @api.depends('store_fname')
    def _compute_b2_remote_key(self):
        for a in self:
            fname = a.store_fname or ''
            a.b2_remote_key = fname[len(PREFIX):].split('/', 1)[-1] if fname.startswith(PREFIX) else False

    @api.depends('store_fname', 'checksum')
    def _compute_b2_local_copy(self):
        for a in self:
            fname = a.store_fname or ''
            if fname.startswith(PREFIX):
                fname = a.checksum[:2] + '/' + a.checksum if a.checksum else ''
            size = 0
            present = False
            if fname and '://' not in fname:
                try:
                    path = a._full_path(fname)
                    present = os.path.isfile(path)
                    size = os.path.getsize(path) if present else 0
                except OSError:
                    pass
            a.b2_local_copy = present
            a.b2_local_bytes = size

    def _b2_is_business_document(self):
        """Conservative boundary: never normalize system assets or framework records."""
        self.ensure_one()
        name = (self.name or '').replace('\\', '/').rsplit('/', 1)[-1]
        ext = os.path.splitext(name)[1].lower()
        model = self.res_model or ''
        return bool(
            self.type == 'binary' and self.res_id and model
            and not self.url and not self.res_field  # Do not change system binary-field assets
            and not model.startswith(('ir.', 'web.', 'bus.', 'base.', 'theme.', 'website.'))
            and model not in ('res.company', 'res.users', 'res.config.settings', 'website')
            and not (self.name or '').lower().startswith(('web.assets', '/web/', 'web/'))
            and ext not in ('.js', '.css', '.map', '.html', '.htm', '.woff', '.woff2', '.ttf', '.otf', '.scss', '.less')
            and (self.mimetype or '').lower() not in (
                'application/javascript', 'text/javascript', 'text/css', 'text/html',
                'application/x-font-ttf', 'font/woff', 'font/woff2')
        )

    @api.model
    def _b2_detect_content_type(self, data, extension='', archive_path=None):
        """Strict signature recognition; extension is NEVER proof of MIME."""
        if data.startswith(b'\xff\xd8\xff'):
            return 'image/jpeg', '.jpg'
        if data.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'image/png', '.png'
        if data.startswith(b'%PDF-'):
            return 'application/pdf', '.pdf'
        if data[:6] in (b'GIF87a', b'GIF89a'):
            return 'image/gif', '.gif'
        if data.startswith(b'BM') and len(data) >= 14:
            return 'image/bmp', '.bmp'
        if data.startswith((b'II*\x00', b'MM\x00*')):
            return 'image/tiff', '.tiff'
        if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
            return 'image/webp', '.webp'
        if len(data) >= 12 and data[4:8] == b'ftyp':
            return 'video/mp4', '.mp4'
        if data.startswith(b'ID3') or (len(data) >= 2 and data[0] == 255 and data[1] & 0xe0 == 0xe0):
            return 'audio/mpeg', '.mp3'
        if data.startswith(b'PK\x03\x04'):
            try:
                with zipfile.ZipFile(archive_path if archive_path else io.BytesIO(data)) as archive:
                    members = set(archive.namelist())
                    if 'word/document.xml' in members and '[Content_Types].xml' in members:
                        return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', '.docx'
                    if 'xl/workbook.xml' in members and '[Content_Types].xml' in members:
                        return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '.xlsx'
                    if 'ppt/presentation.xml' in members and '[Content_Types].xml' in members:
                        return 'application/vnd.openxmlformats-officedocument.presentationml.presentation', '.pptx'
                    if 'mimetype' in members:
                        odf = archive.read('mimetype')
                        mapping = {
                            b'application/vnd.oasis.opendocument.text': ('application/vnd.oasis.opendocument.text', '.odt'),
                            b'application/vnd.oasis.opendocument.spreadsheet': ('application/vnd.oasis.opendocument.spreadsheet', '.ods'),
                            b'application/vnd.oasis.opendocument.presentation': ('application/vnd.oasis.opendocument.presentation', '.odp'),
                        }
                        return mapping.get(odf)
            except (OSError, ValueError, zipfile.BadZipFile, RuntimeError, KeyError):
                return None
        return None

    def _b2_normalize_metadata(self):
        """Identify local business attachments using a bounded header read.

        The repository max_mb controls transfer eligibility; metadata detection has
        no independent total-file-size ceiling. ZIP formats inspect the archive's
        central directory from disk, without reading the entire document into RAM.
        The transfer stage separately validates the complete SHA-1 checksum.
        """
        self.ensure_one()
        a = self.sudo()
        if not a._b2_is_business_document() or (a.store_fname or '').startswith(PREFIX):
            return False
        eligible = self.env['incmd.b2.rule'].sudo().search([
            ('active', '=', True), ('repository_id.active', '=', True)])
        if not any(a.res_model in rule._target_models() for rule in eligible):
            return False
        name = a.name or ''
        extension = os.path.splitext(name)[1].lower()
        if a.mimetype and extension:
            return False
        if not a.file_size or not a.checksum or not a.store_fname:
            return False
        try:
            # Work only with regular local filestore files. Never fetch remote
            # attachments or unpack untrusted data to normalize metadata.
            local_path = a._full_path(a.store_fname)
            if not os.path.isfile(local_path) or os.path.getsize(local_path) != a.file_size:
                return False
            with open(local_path, 'rb') as handle:
                header = handle.read(4096)
            if not header:
                return False
            detected_type = a._b2_detect_content_type(
                header, extension,
                archive_path=local_path if header.startswith(b'PK\x03\x04') else None,
            )
            if not detected_type:
                return False
            detected, suffix = detected_type
            valid_extensions = {'.jpg', '.jpeg'} if suffix == '.jpg' else {suffix}
            if extension and extension not in valid_extensions:
                _logger.warning('B2 MIME mismatch on attachment %s: %s vs %s', a.id, extension, detected)
                return False
            if a.mimetype and a.mimetype != detected:
                _logger.warning('B2 MIME mismatch on attachment %s: %s vs %s', a.id, a.mimetype, detected)
                return False
            changes = {}
            if not a.mimetype:
                changes['mimetype'] = detected
            if not extension:
                changes['name'] = name + suffix
            if changes:
                # Metadata only. Do not change raw, checksum, filestore path,
                # cloud object references or call the transfer hook recursively.
                models.Model.write(a.with_context(b2_internal=True), changes)
                _logger.info('B2 normalized attachment %s fields %s', a.id, ','.join(changes))
            return bool(changes)
        except Exception as exc:
            _logger.warning('B2 normalization skipped for attachment %s (%s)', a.id, type(exc).__name__)
            return False

    def _b2_rule(self, repository_id=None):
        self.ensure_one()
        # Deny technical assets, unlinked uploads, URLs and unknown use by default.
        if self.type != 'binary' or not self.res_model or not self.res_id:
            return self.env['incmd.b2.rule']
        if self.res_model in ('res.company','res.users','res.config.settings','website','website.page','website.menu') or self.res_model.startswith(('ir.', 'web.', 'bus.', 'base.', 'theme.')) or self.url or (self.name or '').startswith('web.assets'):
            return self.env['incmd.b2.rule']
        if self.mimetype in ('application/javascript','text/javascript','text/css','text/html','application/x-font-ttf','font/woff','font/woff2'):
            return self.env['incmd.b2.rule']
        basename = (self.name or '').replace('\\', '/').rsplit('/', 1)[-1]
        ext = basename.rsplit('.', 1)[-1].lower() if '.' in basename else ''
        if ext in ('js','css','map','html','htm','woff','woff2','ttf','otf'):
            return self.env['incmd.b2.rule']
        domain = [('active','=',True),('repository_id.active','=',True)]
        if repository_id:
            domain.append(('repository_id','=',repository_id))
        rules = self.env['incmd.b2.rule'].sudo().search(domain)
        # Specific model, module, then global; sequence/ID break ties.
        rules = rules.sorted(key=lambda r: (2 if r.scope == 'global' else (0 if r.model_id else 1), r.sequence, r.id))
        for r in rules:
            if self.res_model not in r._target_models():
                continue
            mime_filters, extension_filters = r._document_filters()
            allowed_fields = [s.strip() for s in (r.field_names or '').split(',') if s.strip()]
            if r.include_product_images:
                if self.res_model == 'product.template':
                    allowed_fields.append('image_1920')
                elif self.res_model == 'product.product':
                    allowed_fields.append('image_variant_1920')
            if self.res_field and self.res_field not in allowed_fields:
                continue
            if not any(fnmatch.fnmatchcase(self.mimetype or '', p.strip()) for p in mime_filters.split(',') if p.strip()):
                continue
            extensions = [s.strip().lower().lstrip('.') for s in (extension_filters or '').split(',') if s.strip()]
            # Binary fields can have technical names without a file extension.
            # Authorized fields use the MIME check; ordinary documents also check extension.
            if not self.res_field and not ext and not r.allow_extensionless:
                continue
            if not self.res_field and ext and extensions and ext not in extensions:
                continue
            return r
        return self.env['incmd.b2.rule']

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get('b2_internal'):
            records._b2_transfer()
        return records

    def write(self, vals):
        if not self.env.context.get('b2_internal') and {'raw', 'datas', 'db_datas'} & vals.keys():
            vals = dict(vals, b2_thumbnail_key=False, b2_thumbnail_checksum=False,
                        b2_thumbnail_attempts=0, b2_thumbnail_next_try=False, b2_thumbnail_error=False)
        result = super().write(vals)
        if not self.env.context.get('b2_internal') and {'raw','datas','db_datas','res_model','res_id','res_field'} & vals.keys():
            self._b2_transfer()
        return result

    def _b2_log(self, repo, old, key, state, detail=''):
        return self.env['incmd.b2.audit'].sudo().create({'attachment_id': self.id,
            'attachment_number': self.id, 'name': self.name, 'res_model': self.res_model,
            'res_id': self.res_id, 'res_field': self.res_field, 'repository_id': repo.id,
            'old_location': old, 'remote_key': key, 'state': state, 'detail': detail})

    def _b2_object_key(self, repo, digest):
        self.ensure_one()
        folder = (repo.folder or 'attachments').strip('/') or 'attachments'
        environment = repo.storage_environment or 'desarrollo'
        model = re.sub(r'[^A-Za-z0-9_.-]', '_', self.res_model or 'sin_modelo')
        created = fields.Datetime.to_datetime(self.create_date or fields.Datetime.now())
        if created.tzinfo is None:
            created = pytz.UTC.localize(created)
        day = created.astimezone(pytz.timezone(repo.path_timezone))
        # Keep a content-based name; do not expose original document/customer names.
        extension = os.path.splitext(self.name or '')[1].lower()
        if not re.fullmatch(r'\.[a-z0-9]{1,10}', extension):
            extension = ''
        return f"{folder}/{environment}/{model}/{day:%Y}/{day:%Y-%m-%d}/{digest}{extension}"

    def _b2_transfer(self, repository_id=None, from_batch=False, budget=None):
        for original in self:
            a = original.sudo()
            if (a.store_fname or '').startswith(PREFIX):
                continue
            if not a.mimetype or not os.path.splitext(a.name or '')[1]:
                try:
                    with self.env.cr.savepoint():
                        a._b2_normalize_metadata()
                except Exception as exc:
                    _logger.warning('B2 pre-transfer normalization failed for %s (%s)', a.id, type(exc).__name__)
            # Bind failed/queued uploads to their original repository.
            assigned = a.b2_repository_id.id if a.b2_state == 'pending' else None
            if repository_id and assigned and assigned != repository_id:
                continue
            rule = a._b2_rule(assigned) if assigned else a._b2_rule()
            if not rule or (repository_id and rule.repository_id.id != repository_id):
                continue
            repo = rule.repository_id
            if repo.contingency_enabled:
                continue
            if budget is None:
                budget = {'deadline': time.monotonic() + repo.batch_seconds, 'failures': 0}
            if a.b2_state == 'pending':
                if from_batch and not self.env.context.get('b2_retry_mode') and (a.b2_retry_queued or a.b2_attempts > 0):
                    continue
                if a.b2_next_try and a.b2_next_try > fields.Datetime.now():
                    continue
                if repo.max_attempts and a.b2_attempts >= repo.max_attempts:
                    continue
            if a.file_size > repo.max_mb * 1024 * 1024:
                continue
            throttled = budget and (time.monotonic() >= budget['deadline'] )
            throttled = throttled or (from_batch and not self.env.context.get('b2_retry_mode') and not repo._b2_in_window())
            # Non-blocking global lock: one transfer transaction for this database.
            available = False
            if not throttled and (from_batch or repo.upload_mode == 'immediate'):
                self.env.cr.execute('SELECT pg_try_advisory_xact_lock(%s)', [192837463])
                available = self.env.cr.fetchone()[0]
            if throttled or not available:
                a.with_context(b2_internal=True).write({'b2_state': 'pending',
                    'b2_repository_id': repo.id, 'b2_rule_id': rule.id,
                    'b2_next_try': a.b2_next_try or fields.Datetime.now()})
                continue
            old = a.store_fname
            key = ''
            try:
                with self.env.cr.savepoint():
                    self.env.cr.execute('SELECT id FROM ir_attachment WHERE id=%s FOR UPDATE SKIP LOCKED', [a.id])
                    if not self.env.cr.fetchone():
                        continue
                    a.invalidate_recordset(['store_fname','raw','checksum','file_size'])
                    if (a.store_fname or '').startswith(PREFIX):
                        continue
                    old = a.store_fname
                    data = a.raw
                    if data is None or len(data) != a.file_size or hashlib.sha1(data).hexdigest() != a.checksum:
                        raise ValueError('Local checksum mismatch')
                    digest = hashlib.sha256(data).hexdigest()
                    key = a._b2_object_key(repo, digest)
                    # Serialize identical content in this Odoo database without waiting.
                    lock_id = int(hashlib.sha256((repo.endpoint + repo.bucket + key).encode()).hexdigest()[:16], 16) % (2**63)
                    self.env.cr.execute('SELECT pg_try_advisory_xact_lock(%s)', [lock_id])
                    if not self.env.cr.fetchone()[0]:
                        raise ValueError('Identical content is being transferred; retry later')
                    from botocore.exceptions import ClientError
                    exists = True
                    try:
                        repo._call('head_object', Key=key)
                    except ClientError as error:
                        code = error.response.get('Error', {}).get('Code', '')
                        if code not in ('404', 'NoSuchKey', 'NotFound'):
                            raise
                        exists = False
                    if not exists:
                        repo._call('put_object', Key=key, Body=data, ContentType=a.mimetype or 'application/octet-stream',
                            Metadata={'sha256': digest, 'sha1': a.checksum})
                    obj = repo._call('get_object', Key=key)
                    body = obj['Body']
                    try:
                        remote = body.read()
                    finally:
                        body.close()
                    if len(remote) != len(data) or hashlib.sha256(remote).hexdigest() != digest or hashlib.sha1(remote).hexdigest() != a.checksum:
                        raise ValueError('Remote checksum mismatch')
                    models.Model.write(a.with_context(b2_internal=True), {'store_fname': f'{PREFIX}{repo.id}/{key}', 'db_datas': False,
                        'b2_repository_id': repo.id, 'b2_rule_id': rule.id, 'b2_attempts': 0, 'b2_state': 'remote', 'b2_next_try': False, 'b2_retry_queued': False})
                    a.invalidate_recordset(['store_fname','raw','datas'])
                    if a.store_fname != f'{PREFIX}{repo.id}/{key}':
                        raise ValueError('Remote reference was not persisted')
                    a._b2_log(repo, old, key, 'done', 'Reutilizado' if exists else 'Nuevo objeto')
                    if from_batch and time.monotonic() < budget['deadline']:
                        a._b2_prepare_thumbnail(data)

                    if old:
                        # Odoo GC checks remaining references before deleting physical files.
                        a._file_delete(old)
            except Exception as exc:
                if budget is not None:
                    budget['failures'] += 1
                a.with_context(b2_internal=True).write({'b2_state':'pending',
                    'b2_repository_id': repo.id, 'b2_rule_id': rule.id,
                    'b2_attempts': a.b2_attempts + 1,
                    'b2_next_try': fields.Datetime.now() + timedelta(minutes=repo.retry_minutes),
                    'b2_retry_queued': True})
                detail = type(exc).__name__
                if isinstance(exc, AttributeError):
                    detail += ': ' + str(getattr(exc, 'name', None) or 'atributo no disponible')
                a._b2_log(repo, old, key, 'error', detail)
                _logger.warning('B2 transfer deferred for attachment %s (%s)', a.id, type(exc).__name__)

    def _b2_prepare_thumbnail(self, data=None):
        """Independent work: failure never rolls back a verified original."""
        self.ensure_one()
        a = self.sudo()
        if not (a.store_fname or '').startswith(PREFIX) or a.mimetype not in ('image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/bmp', 'image/tiff'):
            return
        if a.b2_thumbnail_key or (a.b2_thumbnail_next_try and a.b2_thumbnail_next_try > fields.Datetime.now()):
            return
        repo = a.b2_repository_id
        if repo.contingency_enabled:
            return
        if repo.max_attempts and a.b2_thumbnail_attempts >= repo.max_attempts:
            return
        try:
            with self.env.cr.savepoint():
                self.env.cr.execute('SELECT id FROM ir_attachment WHERE id=%s FOR UPDATE SKIP LOCKED', [a.id])
                if not self.env.cr.fetchone():
                    return
                from PIL import Image, ImageOps
                import warnings
                source = data if data is not None else a.raw
                # Pillow's pixel limit also applies to decompression bombs.
                with warnings.catch_warnings():
                    warnings.simplefilter('error', Image.DecompressionBombWarning)
                    with Image.open(io.BytesIO(source)) as image:
                        image.seek(0)
                        image = ImageOps.exif_transpose(image)
                        image.thumbnail((512, 512), Image.Resampling.LANCZOS)
                        rgba = image.convert('RGBA')
                        preview = Image.new('RGB', rgba.size, 'white')
                        preview.paste(rgba, mask=rgba.getchannel('A'))
                        output = io.BytesIO()
                        preview.save(output, format='JPEG', quality=80, optimize=True)
                payload = output.getvalue()
                digest = hashlib.sha256(payload).hexdigest()
                key = a.store_fname[len(PREFIX):].split('/', 1)[1] + '.thumb512-v1.jpg'
                repo._call('put_object', Key=key, Body=payload, ContentType='image/jpeg',
                           Metadata={'sha256': digest}, CacheControl='private, max-age=86400')
                a.with_context(b2_internal=True).write({
                    'b2_thumbnail_key': key, 'b2_thumbnail_checksum': digest,
                    'b2_thumbnail_attempts': 0, 'b2_thumbnail_next_try': False,
                    'b2_thumbnail_error': False})
        except Exception as exc:
            a.with_context(b2_internal=True).write({
                'b2_thumbnail_attempts': a.b2_thumbnail_attempts + 1,
                'b2_thumbnail_next_try': fields.Datetime.now() + timedelta(minutes=repo.retry_minutes),
                'b2_thumbnail_error': type(exc).__name__})
            _logger.warning('B2 thumbnail deferred for attachment %s (%s)', a.id, type(exc).__name__)

    def _file_read(self, fname, *args, **kwargs):
        if fname and fname.startswith(PREFIX):
            repo_id, key = fname[len(PREFIX):].split('/', 1)
            repo = self.env['incmd.b2.repository'].sudo().browse(int(repo_id)).exists()
            if not repo:
                raise UserError(_('No existe la configuración del repositorio de este archivo.'))
            try:
                obj = repo._call('get_object', Key=key)
                body = obj['Body']
                try:
                    size = kwargs.get('size', args[0] if args else None)
                    return body.read() if size is None else body.read(size)
                finally:
                    body.close()
            except Exception:
                raise UserError(_('No se pudo recuperar el documento de Backblaze. Intente nuevamente.'))
        return super()._file_read(fname, *args, **kwargs)

    def _file_delete(self, fname):
        if fname and fname.startswith(PREFIX):
            # Do not delete remotely inside a DB transaction: rollback/shared references.
            return
        return super()._file_delete(fname)

    def _b2_stream(self):
        self.ensure_one()
        if self.env.context.get('b2_use_thumbnail') and self.b2_thumbnail_key:
            try:
                obj = self.b2_repository_id.sudo()._call('get_object', Key=self.b2_thumbnail_key)
                body = obj['Body']
                try:
                    data = body.read()
                finally:
                    body.close()
                return Stream(type='data', data=data, size=len(data), mimetype='image/jpeg',
                    download_name='preview.jpg', etag=self.b2_thumbnail_checksum,
                    public=self.public, last_modified=self.write_date)
            except Exception:
                _logger.warning('B2 thumbnail unavailable for attachment %s; using original', self.id)
        data = self.raw
        return Stream(type='data', data=data, size=len(data), mimetype=self.mimetype,
            download_name=self.name, etag=self.checksum, public=self.public, last_modified=self.write_date)

    def _to_http_stream(self):
        self.ensure_one()
        if (self.store_fname or '').startswith(PREFIX):
            return self._b2_stream()
        return super()._to_http_stream()

    @api.model
    def _b2_cleanup(self, audit_ids=None):
        """Select eligible committed paths before limiting the batch; retain shared files."""
        cr = self.env.cr
        cr.execute('SELECT pg_try_advisory_xact_lock(%s)', [192837464])
        if not cr.fetchone()[0]:
            _logger.info('B2 cleanup deferred: another cleanup holds the lock')
            return
        Audit = self.env['incmd.b2.audit'].sudo()
        Audit.flush_model(['state', 'local_released', 'old_location', 'cleanup_next_try'])
        self.env['ir.attachment'].flush_model(['store_fname'])
        params = [fields.Datetime.now()]
        selection = ''
        if audit_ids:
            selection = ' AND a.id = ANY(%s)'
            params.append(list(audit_ids))
        cr.execute("""
            SELECT a.id FROM incmd_b2_audit a
            WHERE a.state = 'done' AND NOT coalesce(a.local_released, false)
              AND (a.cleanup_next_try IS NULL OR a.cleanup_next_try <= %s)
              AND NOT EXISTS (
                  SELECT 1 FROM ir_attachment i WHERE i.store_fname = a.old_location
              )
        """ + selection + ' ORDER BY a.id ASC LIMIT 20', params)
        audits = Audit.browse([row[0] for row in cr.fetchall()])
        if not audits:
            _logger.info('B2 cleanup: no eligible paths; shared paths remain pending')
            return
        # Acquire the GC-compatible reference lock in a savepoint so timeout
        # leaves the transaction usable. Successful lock lasts until caller commit.
        try:
            with cr.savepoint():
                cr.execute("SELECT current_setting('lock_timeout')")
                previous_timeout = cr.fetchone()[0]
                cr.execute("SET LOCAL lock_timeout = '2s'")
                cr.execute('LOCK ir_attachment IN SHARE MODE')
                cr.execute("SELECT set_config('lock_timeout', %s, true)", [previous_timeout])
        except Exception as exc:
            _logger.warning('B2 cleanup reference lock deferred (%s)', type(exc).__name__)
            return
        released = 0
        for log in audits:
            try:
                with cr.savepoint():
                    old = log.old_location
                    if old:
                        if not re.fullmatch(r'[0-9a-f]{2}/[0-9a-f]{40}', old) or old[:2] != old[3:5]:
                            raise ValueError('Ruta histórica inválida; se conserva el archivo')
                        # Recheck under the table lock, including ORM-hidden references.
                        cr.execute('SELECT 1 FROM ir_attachment WHERE store_fname=%s LIMIT 1', [old])
                        if cr.fetchone():
                            log.write({'cleanup_next_try': fields.Datetime.now() + timedelta(minutes=30),
                                       'cleanup_error': 'El archivo todavía tiene referencias locales'})
                            continue
                        path = self._full_path(old)
                        if os.path.islink(path):
                            raise ValueError('Enlace simbólico; se conserva el archivo')
                        if os.path.lexists(path):
                            if not os.path.isfile(path):
                                raise ValueError('La ruta no es un archivo regular')
                            os.unlink(path)
                    log.write({'local_released': True, 'cleanup_next_try': False,
                               'cleanup_error': False})
                    released += 1
            except Exception as exc:
                # Failure of one path does not roll back successful predecessors.
                # If unlink succeeded but DB write failed, next try confirms absence.
                try:
                    with cr.savepoint():
                        log.write({'cleanup_attempts': log.cleanup_attempts + 1,
                                   'cleanup_next_try': fields.Datetime.now() + timedelta(minutes=30),
                                   'cleanup_error': ('%s: %s' % (type(exc).__name__, str(exc)))[:500]})
                except Exception:
                    _logger.exception('B2 cleanup could not store retry for audit %s', log.id)
                _logger.warning('B2 cleanup deferred for audit %s (%s)', log.id, type(exc).__name__)
        _logger.info('B2 cleanup: selected=%s confirmed=%s', len(audits), released)

    @api.model
    def _b2_retry_batch(self, repository_ids=None):
        # Own schedule, same global transfer lock as normal migration. Never clean here.
        self.env.cr.execute('SELECT pg_try_advisory_xact_lock(%s)', [192837463])
        if not self.env.cr.fetchone()[0]:
            return
        repos = self.env['incmd.b2.repository'].sudo().search(
            [('active', '=', True), ('automatic_enabled', '=', True),
             ('retry_enabled', '=', True)] +
            ([('id', 'in', repository_ids)] if repository_ids else []))
        for repo in repos:
            if repo.contingency_enabled:
                continue
            budget = {'deadline': time.monotonic() + repo.retry_batch_seconds, 'failures': 0}
            domain = [
                ('b2_state', '=', 'pending'), ('b2_repository_id', '=', repo.id),
                ('type', '=', 'binary'), ('file_size', '<=', repo.max_mb * 1024 * 1024),
                ('b2_attempts', '>', 0),
                '|', ('b2_next_try', '=', False), ('b2_next_try', '<=', fields.Datetime.now())]
            if repo.max_attempts:
                domain.append(('b2_attempts', '<', repo.max_attempts))
            pending = self.sudo().search(domain, limit=repo.retry_batch_size, order='b2_next_try asc, id asc')
            for attachment in pending:
                if time.monotonic() >= budget['deadline']:
                    break
                if repo.batch_failure_limit != -1 and budget['failures'] >= repo.batch_failure_limit:
                    break
                try:
                    with self.env.cr.savepoint():
                        # Historical v45 failed records (attempts > 0) join retry queue.
                        attachment.with_context(b2_internal=True).write({'b2_retry_queued': True})
                        attachment.with_context(b2_retry_mode=True)._b2_transfer(
                            repo.id, from_batch=True, budget=budget)
                except Exception as exc:
                    _logger.warning('B2 independent retry error for attachment %s (%s)',
                                    attachment.id, type(exc).__name__)
                    budget['failures'] += 1
                    # Retain the record for the next retry rather than losing the job.
                    with self.env.cr.savepoint():
                        attachment.with_context(b2_internal=True).write({
                            'b2_next_try': fields.Datetime.now() + timedelta(minutes=repo.retry_minutes)})

    @api.model
    def _b2_batch(self, repository_ids=None):
        self.env.cr.execute('SELECT pg_try_advisory_xact_lock(%s)', [192837463])
        if not self.env.cr.fetchone()[0]:
            return
        repos = self.env['incmd.b2.repository'].sudo().search([('active','=',True)] + ([('id','in',repository_ids)] if repository_ids else []))
        for repo in repos:
            if repo.contingency_enabled:
                continue
            if not repo._b2_in_window():
                continue
            self.env.cr.execute('SELECT pg_try_advisory_xact_lock(%s, %s)', [192837461, repo.id])
            if not self.env.cr.fetchone()[0]:
                continue
            # Upgrade legacy pending records without a recorded destination once.
            legacy = self.sudo().search([('b2_state','=','pending'), ('b2_repository_id','=',False)], limit=repo.batch_size, order='id')
            for attachment in legacy:
                rule = attachment._b2_rule()
                if rule:
                    attachment.with_context(b2_internal=True).write({'b2_repository_id': rule.repository_id.id, 'b2_rule_id': rule.id})
            budget = {'deadline': time.monotonic() + repo.batch_seconds, 'failures': 0}
            rules = repo.rule_ids.filtered('active')
            models_allowed = list({model for rule in rules for model in rule._target_models()})
            attempt_domain = [('b2_attempts','<',repo.max_attempts)] if repo.max_attempts else []
            thumbnails = self.sudo().search([
                ('b2_repository_id', '=', repo.id), ('store_fname', 'like', PREFIX + '%'),
                ('b2_thumbnail_key', '=', False),
                ('mimetype', 'in', ['image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/bmp', 'image/tiff']),
                '|', ('b2_thumbnail_next_try', '=', False), ('b2_thumbnail_next_try', '<=', fields.Datetime.now())
            ] + ([('b2_thumbnail_attempts', '<', repo.max_attempts)] if repo.max_attempts else []),
                limit=min(5, max(1, repo.batch_size // 4)), order='id')
            thumbnail_work = 0
            for attachment in thumbnails:
                if time.monotonic() >= budget['deadline'] or not repo._b2_in_window():
                    break
                attachment._b2_prepare_thumbnail()
                thumbnail_work += 1
            transfer_limit = max(0, repo.batch_size - thumbnail_work)
            if not transfer_limit:
                continue
            pending = self.sudo().search(attempt_domain + [('b2_retry_queued','=',False), ('b2_attempts','=',0), ('b2_state','=','pending'),('b2_repository_id','=',repo.id),('res_model','in',models_allowed),('file_size','<=',repo.max_mb * 1024 * 1024),
                '|',('b2_next_try','=',False),('b2_next_try','<=',fields.Datetime.now())], limit=transfer_limit, order='id')
            for item in pending:
                if time.monotonic() >= budget['deadline'] or (repo.batch_failure_limit != -1 and budget['failures'] >= repo.batch_failure_limit):
                    break
                item._b2_transfer(repo.id, from_batch=True, budget=budget)
            remaining = transfer_limit - len(pending)
            if not repo.migration_enabled or remaining <= 0:
                continue
            for rule in rules:
                if remaining <= 0:
                    break
                # Scan bounded pages of metadata. Only eligible transfer attempts
                # consume the migration quota; rejected files remain local.
                cursor = rule.cursor_id
                stopped = False
                while remaining > 0 and not stopped:
                    if (time.monotonic() >= budget['deadline'] or
                            (repo.batch_failure_limit != -1 and budget['failures'] >= repo.batch_failure_limit) or
                            not repo._b2_in_window()):
                        break
                    records = self.sudo().search([
                        ('id', '>', cursor), ('res_model', 'in', rule._target_models()),
                        ('type', '=', 'binary'), ('b2_state', '!=', 'pending'),
                        '|', ('store_fname', '=', False),
                        ('store_fname', 'not like', PREFIX + '%')],
                        order='id', limit=500)
                    if not records:
                        break
                    for attachment in records:
                        if (time.monotonic() >= budget['deadline'] or
                                (repo.batch_failure_limit != -1 and budget['failures'] >= repo.batch_failure_limit) or
                                not repo._b2_in_window()):
                            stopped = True
                            break
                        if not attachment.mimetype or not os.path.splitext(attachment.name or '')[1]:
                            try:
                                with self.env.cr.savepoint():
                                    attachment._b2_normalize_metadata()
                            except Exception as exc:
                                _logger.warning('B2 historical metadata deferred %s: %s', attachment.id, type(exc).__name__)
                        selected = attachment._b2_rule()
                        if (selected and selected.repository_id.id == repo.id and
                                attachment.file_size <= repo.max_mb * 1024 * 1024):
                            attachment._b2_transfer(repo.id, from_batch=True, budget=budget)
                            remaining -= 1
                        cursor = attachment.id
                        if remaining <= 0:
                            break
                    # Never advance past records not examined before the deadline.
                    if cursor != rule.cursor_id:
                        rule.cursor_id = cursor

class Binary(models.AbstractModel):
    _inherit = 'ir.binary'

    def _get_image_stream_from(self, record, field_name='raw', filename=None, filename_field='name',
                               mimetype=None, default_mimetype='image/png', placeholder=None,
                               width=0, height=0, crop=False, quality=0):
        from odoo.http import request
        # Sized image routes only. Full view, downloads and mail retain originals.
        use_thumbnail = bool((width or height) and 0 <= width <= 512 and 0 <= height <= 512 and not crop)
        if request and request.params.get('download'):
            use_thumbnail = False
        binary = self.with_context(b2_use_thumbnail=use_thumbnail)
        return super(Binary, binary)._get_image_stream_from(
            record, field_name, filename, filename_field, mimetype, default_mimetype,
            placeholder, width, height, crop, quality)

    def _record_to_stream(self, record, field_name):
        if record._name == 'ir.attachment' and field_name in ('raw','datas','db_datas') and (record.store_fname or '').startswith(PREFIX):
            return record.with_context(b2_use_thumbnail=self.env.context.get('b2_use_thumbnail', False))._b2_stream()
        # Odoo 17 Stream.from_attachment bypasses attachment hooks.
        if record._name != 'ir.attachment' and record._fields[field_name].attachment:
            record.check_field_access_rights('read', [field_name])
            a = self.env['ir.attachment'].sudo().search([('res_model','=',record._name),('res_id','=',record.id),('res_field','=',field_name)], limit=1)
            if a and (a.store_fname or '').startswith(PREFIX):
                return a.with_context(b2_use_thumbnail=self.env.context.get('b2_use_thumbnail', False))._b2_stream()
        return super()._record_to_stream(record, field_name)




class StorageModuleContingency(models.Model):
    _inherit = 'ir.module.module'

    def button_immediate_uninstall(self):
        if any(module.name == 'incmd_b2_storage' for module in self):
            if self.env['ir.attachment'].sudo().search_count([
                    ('store_fname', '=like', PREFIX + '%')], limit=1):
                raise UserError(_('Recupere todos los adjuntos remotos al filestore antes de desinstalar el módulo Backblaze.'))
        return super().button_immediate_uninstall()
