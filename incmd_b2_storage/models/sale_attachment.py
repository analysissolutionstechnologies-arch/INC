import os
import ast
import io
import zipfile
from lxml import etree
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.osv import expression


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    b2_document_ids = fields.Many2many(
        'ir.attachment', compute='_compute_b2_document_ids',
        string='Documentos cargados', compute_sudo=False)

    def _b2_document_domain(self):
        self.ensure_one()
        domain = [('res_model', '=', 'sale.order'), ('res_id', '=', self.id),
                  ('res_field', '=', False)]
        studio = self.env['ir.attachment']._fields.get('x_studio_adjuntos_pedido')
        if studio and studio.type == 'many2one' and studio.comodel_name == 'sale.order':
            domain = expression.OR([[('x_studio_adjuntos_pedido', '=', self.id)], domain])
        relation = self._fields.get('x_studio_adjuntos')
        if relation and relation.type == 'many2many' and relation.comodel_name == 'ir.attachment':
            domain = expression.OR([[('id', 'in', self.x_studio_adjuntos.ids)], domain])
        # Resolve project links using the caller's access rules. Keep attachment
        # ownership on the task and avoid calling its combined quotation domain.
        Task = self.env['project.task']
        links = []
        for name in ('x_studio_pedido', 'sale_order_id'):
            field = Task._fields.get(name)
            if field and field.type == 'many2one' and field.comodel_name == 'sale.order':
                links.append([(name, '=', self.id)])
        line = Task._fields.get('sale_line_id')
        if line and line.type == 'many2one' and line.comodel_name == 'sale.order.line':
            links.append([('sale_line_id.order_id', '=', self.id)])
        if links and Task.check_access_rights('read', raise_exception=False):
            tasks = Task.search(expression.OR(links))
            if tasks:
                task_domains = [[('res_model', '=', 'project.task'),
                                 ('res_id', 'in', tasks.ids), ('res_field', '=', False)]]
                messages = self.env['mail.message'].search([
                    ('model', '=', 'project.task'), ('res_id', 'in', tasks.ids)])
                attachment_ids = messages.mapped('attachment_ids').ids
                if attachment_ids:
                    task_domains.append([('id', 'in', attachment_ids)])
                domain = expression.OR([domain] + task_domains)
        return expression.AND([[('type', '=', 'binary')], domain])

    def _compute_b2_document_ids(self):
        for order in self:
            if not order.id or not isinstance(order.id, int):
                order.b2_document_ids = False
                continue
            order.check_access_rights('read')
            order.check_access_rule('read')
            order.b2_document_ids = self.env['ir.attachment'].search(
                order._b2_document_domain(), order='id desc')

    def b2_get_carousel_documents(self):
        self.ensure_one()
        self.check_access_rights('read')
        self.check_access_rule('read')
        # Return only metadata. Content follows normal Odoo attachment checks.
        return self.env['ir.attachment'].search_read(
            self._b2_document_domain(),
            ['name', 'mimetype', 'write_date'], order='id desc')

    def action_b2_view_documents(self):
        self.ensure_one()
        self.check_access_rights('read')
        self.check_access_rule('read')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Documentos de %s') % self.name,
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,tree,form',
            'views': [
                (self.env.ref('incmd_b2_storage.sale_document_gallery').id, 'kanban'),
                (self.env.ref('incmd_b2_storage.sale_document_list').id, 'tree'),
                (self.env.ref('incmd_b2_storage.sale_attachment_upload_form').id, 'form'),
            ],
            'domain': self._b2_document_domain(),
            'context': {'create': False, 'edit': False, 'delete': False},
            'target': 'new',
        }

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        result = super().get_view(view_id=view_id, view_type=view_type, **options)
        if view_type == 'form':
            arch = etree.fromstring(result['arch'])
            for node in arch.xpath("//field[@name='x_studio_adjuntos']"):
                previous = node.get('context', '{}').strip()
                # Odoo's browser evaluator accepts dictionary literals, not dict().
                # Preserve Studio expressions without evaluating them server-side.
                try:
                    parsed = ast.parse(previous, mode='eval').body
                except SyntaxError:
                    parsed = None
                if not isinstance(parsed, ast.Dict):
                    # Leave nonliteral custom contexts intact; order hooks still
                    # link orphan attachments after saving the relation.
                    continue
                extra = "'default_res_model': 'sale.order', 'default_res_id': id, 'default_type': 'binary', 'b2_sale_upload': True, 'form_view_ref': 'incmd_b2_storage.sale_attachment_upload_form'"
                content = previous[1:-1].strip().rstrip(',')
                node.set('context', '{' + content + (', ' if content else '') + extra + '}')
            # Add the gallery after Odoo resolves the installed custom form.
            # No inherited sale view is loaded/validated during module upgrade.
            notebooks = arch.xpath('//sheet/notebook')
            if notebooks and not arch.xpath("//page[@name='b2_documents']"):
                page = etree.fromstring('<page name="b2_documents" string="Documentos cargados"><widget name="b2_document_carousel"/></page>')
                notebooks[0].append(page)
            result['arch'] = etree.tostring(arch, encoding='unicode')
        return result

    def _b2_link_sale_documents(self):
        field = self._fields.get('x_studio_adjuntos')
        if not field or field.type != 'many2many' or field.comodel_name != 'ir.attachment':
            return
        for order in self:
            for attachment in order.x_studio_adjuntos:
                # Never take ownership from another business record.
                if attachment.res_id or attachment.res_model not in (False, 'sale.order'):
                    continue
                if self.sudo().search_count([('x_studio_adjuntos', 'in', attachment.ids)], limit=2) != 1:
                    continue
                attachment.write({'res_model': 'sale.order', 'res_id': order.id})

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._b2_link_sale_documents()
        return orders

    def write(self, vals):
        result = super().write(vals)
        if 'x_studio_adjuntos' in vals:
            self._b2_link_sale_documents()
        return result

    @api.model
    def _b2_repair_sale_documents(self):
        field = self._fields.get('x_studio_adjuntos')
        self.env['ir.attachment'].sudo()._b2_repair_studio_sale_documents()
        if not field or field.type != 'many2many' or field.comodel_name != 'ir.attachment':
            return
        parameters = self.env['ir.config_parameter'].sudo()
        cursor = int(parameters.get_param('incmd_b2_storage.sale_link_cursor', '0'))
        orders = self.sudo().search([('id', '>', cursor), ('x_studio_adjuntos', '!=', False)], order='id', limit=100)
        orders.with_context(b2_internal=True)._b2_link_sale_documents()
        if orders:
            parameters.set_param('incmd_b2_storage.sale_link_cursor', orders[-1].id)


class SaleAttachment(models.Model):
    _inherit = 'ir.attachment'

    def b2_get_odt_preview(self):
        self.ensure_one()
        self.check_access_rights('read')
        self.check_access_rule('read')
        if not (self.name or '').lower().endswith('.odt') or self.type != 'binary':
            raise ValidationError(_('El archivo no es un documento ODT.'))
        if self.file_size > 20 * 1024 * 1024:
            raise ValidationError(_('El documento supera el tamaño permitido para la vista previa.'))
        try:
            with zipfile.ZipFile(io.BytesIO(self.raw)) as archive:
                if archive.getinfo('content.xml').file_size > 5 * 1024 * 1024:
                    raise ValueError('size')
                root = etree.fromstring(archive.read('content.xml'),
                    parser=etree.XMLParser(resolve_entities=False, no_network=True))
            ns = {'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
                  'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0'}
            paragraphs = root.xpath('//office:body/office:text//text:p | //office:body/office:text//text:h', namespaces=ns)
            return '\n\n'.join(''.join(node.itertext()) for node in paragraphs)[:200000]
        except (zipfile.BadZipFile, KeyError, ValueError, etree.XMLSyntaxError):
            raise ValidationError(_('No se pudo leer la vista previa del documento ODT.'))

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        result = super().get_view(view_id=view_id, view_type=view_type, **options)
        if view_type == 'form' and 'x_studio_adjuntos_pedido' in self._fields:
            arch = etree.fromstring(result['arch'])
            if arch.get('string') == 'Cargar documento':
                node = etree.SubElement(arch, 'field', name='x_studio_adjuntos_pedido', invisible='1')
                result['arch'] = etree.tostring(arch, encoding='unicode')
        return result

    @api.model
    def _b2_configure_studio_sale_action(self):
        """Only adjust attachment actions explicitly scoped to our Studio field."""
        field = self._fields.get('x_studio_adjuntos_pedido')
        if not field or field.type != 'many2one' or field.comodel_name != 'sale.order':
            return
        view = self.env.ref('incmd_b2_storage.sale_attachment_upload_form')
        actions = self.env['ir.actions.act_window'].sudo().search([
            ('res_model', '=', 'ir.attachment'),
            ('domain', 'ilike', 'x_studio_adjuntos_pedido'),
        ])
        for action in actions:
            try:
                parsed = ast.parse(action.context or '{}', mode='eval').body
            except SyntaxError:
                continue
            if not isinstance(parsed, ast.Dict):
                continue
            overrides = {
                'default_res_model': "'sale.order'", 'default_res_id': 'active_id',
                'default_x_studio_adjuntos_pedido': 'active_id',
                'default_type': "'binary'", 'b2_sale_upload': 'True',
                'form_view_ref': repr(view.get_external_id()[view.id]),
            }
            entries = [(k, v) for k, v in zip(parsed.keys, parsed.values)
                       if not isinstance(k, ast.Constant) or k.value not in overrides]
            entries.extend((ast.Constant(key), ast.parse(value, mode='eval').body)
                           for key, value in overrides.items())
            context = ast.unparse(ast.Dict(keys=[k for k, v in entries], values=[v for k, v in entries]))
            action.write({'context': context})
            form = action.view_ids.filtered(lambda item: item.view_mode == 'form')
            if form:
                form.write({'view_id': view.id})
            else:
                self.env['ir.actions.act_window.view'].sudo().create({
                    'act_window_id': action.id, 'view_mode': 'form',
                    'view_id': view.id, 'sequence': 20,
                })

    @api.model
    def _b2_studio_sale_values(self, values):
        values = dict(values)
        field = self._fields.get('x_studio_adjuntos_pedido')
        order_id = values.get('x_studio_adjuntos_pedido')
        if field and field.type == 'many2one' and field.comodel_name == 'sale.order' and order_id:
            if not values.get('res_id') and values.get('res_model') in (False, None, 'sale.order'):
                if not values.get('url') and not values.get('public') and values.get('type', 'binary') == 'binary':
                    order = self.env['sale.order'].browse(order_id).exists()
                    if order:
                        order.check_access_rights('read')
                        order.check_access_rule('read')
                        values.update(res_model='sale.order', res_id=order.id)
        return values

    def _b2_bind_studio_sale_documents(self):
        field = self._fields.get('x_studio_adjuntos_pedido')
        if not field or field.type != 'many2one' or field.comodel_name != 'sale.order':
            return
        for attachment in self:
            if attachment.res_id or attachment.res_model not in (False, 'sale.order'):
                continue
            if attachment.url or attachment.public or attachment.type != 'binary':
                continue
            order = attachment.x_studio_adjuntos_pedido.exists()
            if order:
                attachment.with_context(b2_internal=True).write({'res_model': 'sale.order', 'res_id': order.id})
                if not (attachment.store_fname or '').startswith('b2v2://'):
                    rule = attachment._b2_rule()
                    if rule:
                        attachment.with_context(b2_internal=True).write({
                            'b2_state': 'pending', 'b2_repository_id': rule.repository_id.id,
                            'b2_rule_id': rule.id, 'b2_next_try': False,
                        })

    @api.model
    def _b2_repair_studio_sale_documents(self):
        field = self._fields.get('x_studio_adjuntos_pedido')
        if not field or field.type != 'many2one' or field.comodel_name != 'sale.order':
            return
        parameters = self.env['ir.config_parameter'].sudo()
        cursor = int(parameters.get_param('incmd_b2_storage.studio_sale_link_cursor', '0'))
        attachments = self.sudo().search([
            ('id', '>', cursor), ('x_studio_adjuntos_pedido', '!=', False),
            ('res_id', '=', False), ('res_model', 'in', [False, 'sale.order']),
            ('type', '=', 'binary'), ('url', '=', False), ('public', '=', False),
        ], order='id', limit=100)
        attachments._b2_bind_studio_sale_documents()
        if attachments:
            parameters.set_param('incmd_b2_storage.studio_sale_link_cursor', attachments[-1].id)

    def _b2_validate_sale_upload(self):
        allowed = {'jpg', 'jpeg', 'png', 'pdf', 'odt', 'docx', 'xlsx'}
        # The configurable catalog also governs the special quotation upload.
        # Read only configuration with sudo; attachment access remains unchanged.
        for document_type in self.env['incmd.b2.document.type'].sudo().search([]):
            allowed.update(token.strip().lower().lstrip('.')
                           for token in (document_type.extensions or '').split(',')
                           if token.strip().lstrip('.'))
        for attachment in self:
            extension = os.path.splitext(attachment.name or '')[1].lower().lstrip('.')
            if attachment.type != 'binary' or not attachment.file_size:
                raise ValidationError(_('Seleccione un archivo antes de guardar.'))
            if extension not in allowed:
                raise ValidationError(_('Formato no permitido. Extensiones admitidas: %s') % ', '.join(sorted(allowed)))
            expected = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'pdf': 'application/pdf'}
            if extension in expected and attachment.mimetype != expected[extension]:
                raise ValidationError(_('El contenido del archivo no corresponde a su extensión.'))
            if extension in ('odt', 'docx', 'xlsx'):
                try:
                    with zipfile.ZipFile(io.BytesIO(attachment.raw)) as archive:
                        names = set(archive.namelist())
                        valid = ('word/document.xml' in names if extension == 'docx' else
                                 'xl/workbook.xml' in names if extension == 'xlsx' else
                                 'mimetype' in names and archive.read('mimetype') == b'application/vnd.oasis.opendocument.text')
                        if not valid:
                            raise ValueError('format')
                except (zipfile.BadZipFile, ValueError, KeyError):
                    raise ValidationError(_('El contenido del documento no corresponde a su extensión.'))

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [self._b2_studio_sale_values(vals) for vals in vals_list]
        if not self.env.context.get('b2_sale_upload'):
            return super().create(vals_list)
        # Validate locally before attempting an external upload.
        records = super(SaleAttachment, self.with_context(b2_internal=True)).create(vals_list)
        # Normalize missing metadata before validation; never trust extension alone.
        for attachment in records:
            if not attachment.mimetype and attachment._b2_is_business_document():
                attachment._b2_normalize_metadata()
        records._b2_validate_sale_upload()
        records._b2_transfer()
        return records.with_env(self.env)

    def write(self, vals):
        if not self.env.context.get('b2_sale_upload') or not ({'datas', 'raw', 'name', 'type'} & vals.keys()):
            result = super().write(vals)
            if 'x_studio_adjuntos_pedido' in vals and not self.env.context.get('b2_internal'):
                self._b2_bind_studio_sale_documents()
                self._b2_transfer()
            return result
        vals = dict(vals)
        if {'datas', 'raw'} & vals.keys():
            vals.update(b2_thumbnail_key=False, b2_thumbnail_checksum=False, b2_thumbnail_attempts=0, b2_thumbnail_next_try=False, b2_thumbnail_error=False)
        result = super(SaleAttachment, self.with_context(b2_internal=True)).write(vals)
        self._b2_bind_studio_sale_documents()
        for attachment in self:
            if not attachment.mimetype and attachment._b2_is_business_document():
                attachment._b2_normalize_metadata()
        self._b2_validate_sale_upload()
        self._b2_transfer()
        return result
