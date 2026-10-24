# Este archivo no se utiliza actualmente.
#
# import markupsafe
#
# from odoo import models
#
#
# class HelpdeskTicket(models.Model):
#     _inherit = "helpdesk.ticket"
#
#     _mail_post_access = "read"
#
#     def _message_post_after_hook(self, message, msg_vals):
#         result = super()._message_post_after_hook(message, msg_vals)
#
#         backblaze_attachments = message.attachment_ids.sudo().filtered('external_url')
#         if not backblaze_attachments:
#             return result
#
#         links_body = self._get_backblaze_links_body(backblaze_attachments)
#         message.sudo().write({
#             'attachment_ids': [(3, attachment.id) for attachment in backblaze_attachments],
#             'body': markupsafe.Markup(message.body or '') + links_body,
#         })
#         return result