from lxml import etree
from odoo import api, models
from odoo.osv import expression


class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        result = super().get_view(view_id=view_id, view_type=view_type, **options)
        if view_type == 'form':
            arch = etree.fromstring(result['arch'])
            sheets = arch.xpath('//sheet')
            if sheets and not arch.xpath("//page[@name='b2_project_documents']"):
                notebooks = sheets[0].xpath('./notebook')
                notebook = notebooks[0] if notebooks else etree.SubElement(sheets[0], 'notebook')
                page = etree.SubElement(notebook, 'page', name='b2_project_documents',
                                        string='Documentos para validar')
                etree.SubElement(page, 'widget', name='b2_project_document_carousel')
            result['arch'] = etree.tostring(arch, encoding='unicode')
        return result

    def _b2_project_document_domain(self):
        self.ensure_one()
        self.check_access_rights('read')
        self.check_access_rule('read')
        domains = [[('res_model', '=', self._name), ('res_id', '=', self.id),
                    ('res_field', '=', False)]]
        # Include files on readable chatter messages and custom document relations.
        messages = self.env['mail.message'].search([
            ('model', '=', self._name), ('res_id', '=', self.id)])
        linked_ids = set(messages.mapped('attachment_ids').ids)
        for name, field in self._fields.items():
            if field.type in ('many2many', 'one2many') and field.comodel_name == 'ir.attachment':
                linked_ids.update(self[name].ids)
        if linked_ids:
            domains.append([('id', 'in', sorted(linked_ids))])
        # Some installations display quotation documents through sale_task_attachment.
        # Read their original relation without reassigning ownership or copying files.
        orders = self.env['sale.order']
        studio_order = self._fields.get('x_studio_pedido')
        if studio_order and studio_order.type == 'many2one' and studio_order.comodel_name == 'sale.order':
            orders |= self.x_studio_pedido
        sale_order = self._fields.get('sale_order_id')
        if sale_order and sale_order.comodel_name == 'sale.order':
            orders |= self.sale_order_id
        sale_line = self._fields.get('sale_line_id')
        if sale_line and sale_line.comodel_name == 'sale.order.line':
            orders |= self.sale_line_id.order_id
        for order in orders:
            order.check_access_rights('read')
            order.check_access_rule('read')
            domains.append(order._b2_document_domain())
        return expression.AND([[('type', '=', 'binary')], expression.OR(domains)])

    def b2_get_carousel_documents(self):
        return self.env['ir.attachment'].search_read(
            self._b2_project_document_domain(),
            ['name', 'mimetype', 'write_date'], order='id desc')

    def _get_mail_thread_data(self, *args, **kwargs):
        data = super()._get_mail_thread_data(*args, **kwargs)
        # Extend only an attachment response requested by the native chatter.
        # Keep Odoo's followers/messages/access information untouched.
        if isinstance(data, dict) and 'attachments' in data:
            self.ensure_one()
            attachments = self.env['ir.attachment'].search(
                self._b2_project_document_domain(), order='id desc')
            known = {item['id'] for item in data['attachments']}
            extra = attachments.filtered(lambda attachment: attachment.id not in known)
            data['attachments'] = data['attachments'] + extra._attachment_format()
        return data
