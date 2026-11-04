from odoo import models, _
from odoo.exceptions import AccessError

class Attachment(models.Model):
    _inherit = 'ir.attachment'

    def _request_evidence_locked(self):
        # sudo solo para detectar protección; nunca devuelve datos al solicitante.
        if not self.ids: return False
        original = self.env['incmd.request'].sudo().search_count([
            ('state','!=','draft'),('original_attachment_ids','in',self.ids)])
        evidence = self.env['incmd.request.history'].sudo().search_count([('attachment_ids','in',self.ids)])
        messages = self.env['mail.message'].sudo().search([
            ('model','=','incmd.request'),('attachment_ids','in',self.ids)])
        chatter = self.env['incmd.request'].sudo().search_count([
            ('id','in',messages.mapped('res_id')),('state','!=','draft')]) if messages else 0
        return bool(original or evidence or chatter)

    def write(self, vals):
        protected = {'name','datas','raw','db_datas','store_fname','res_model','res_id','res_field','mimetype','type','url','public','access_token'}
        if protected.intersection(vals) and self._request_evidence_locked():
            raise AccessError(_('Los adjuntos originales y las evidencias registradas son inmutables.'))
        return super().write(vals)

    def unlink(self):
        if self._request_evidence_locked(): raise AccessError(_('No puede eliminar evidencia de una solicitud enviada.'))
        return super().unlink()

class Message(models.Model):
    _inherit = 'mail.message'
    def _is_request_locked(self):
        linked = self.filtered(lambda m:m.model == 'incmd.request' and m.res_id)
        return bool(self.env['incmd.request'].sudo().search_count([('id','in',linked.mapped('res_id')),('state','!=','draft')])) if linked else False
    def write(self, vals):
        if {'body','attachment_ids','model','res_id','author_id','date','subject'}.intersection(vals) and self._is_request_locked():
            raise AccessError(_('El seguimiento enviado se conserva sin cambios. Agregue una nueva aclaración.'))
        return super().write(vals)
    def unlink(self):
        if self._is_request_locked(): raise AccessError(_('No se elimina el seguimiento de solicitudes enviadas.'))
        return super().unlink()
