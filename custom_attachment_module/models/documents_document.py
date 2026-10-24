from odoo import models, api, fields


class DocumentsDocument(models.Model):
    _inherit = 'documents.document'

    has_external_url = fields.Boolean('Has Backblaze URL', compute='_compute_has_external_url')

    @api.depends('attachment_id', 'attachment_id.external_url')
    def _compute_has_external_url(self):
        for record in self:
            attachment = record.attachment_id.sudo()
            record.has_external_url = bool(attachment.external_url)

    # def action_open_backblaze_url(self):
    #     """Abre la URL de Backblaze del attachment en una nueva pestaña."""
    #     self.ensure_one()
    #     attachment = self.attachment_id.sudo()
    #     if not attachment.external_url:
    #         return False
    #     return {
    #         'type': 'ir.actions.act_url',
    #         'url': f'/web/content/backblaze_download/{attachment.id}',
    #         'target': 'new',
    #     }
