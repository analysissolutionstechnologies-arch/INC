import markupsafe

from odoo import models


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    # def _process_attachments_for_post(self, attachments, attachment_ids, message_values):
    #     result = super()._process_attachments_for_post(attachments, attachment_ids, message_values)

    #     attachment_commands = result.get('attachment_ids') or []
    #     linked_attachment_ids = self._get_linked_attachment_ids(attachment_commands)
    #     if not linked_attachment_ids:
    #         return result

    #     backblaze_attachments = self.env['ir.attachment'].sudo().browse(linked_attachment_ids).filtered('external_url')
    #     if not backblaze_attachments:
    #         return result

    #     backblaze_ids = set(backblaze_attachments.ids)
    #     result['attachment_ids'] = [
    #         command for command in attachment_commands
    #         if self._get_linked_attachment_id(command) not in backblaze_ids
    #     ]

    #     body = result.get('body', message_values.get('body') or '')
    #     result['body'] = markupsafe.Markup(body) + self._get_backblaze_links_body(backblaze_attachments)
    #     return result

    # def _get_linked_attachment_ids(self, attachment_commands):
    #     return [
    #         attachment_id
    #         for attachment_id in (self._get_linked_attachment_id(command) for command in attachment_commands)
    #         if attachment_id
    #     ]

    # def _get_linked_attachment_id(self, command):
    #     if isinstance(command, int):
    #         return command
    #     if isinstance(command, (list, tuple)) and len(command) >= 2 and command[0] == 4:
    #         return command[1]
    #     return False

    # def _get_backblaze_links_body(self, attachments):
    #     links = []
    #     for attachment in attachments:
    #         display_name = markupsafe.escape(attachment.original_name or attachment.name or 'archivo')
    #         download_path = f'/web/content/backblaze_download/{attachment.id}'
    #         links.append(
    #             markupsafe.Markup(
    #                 '<p><a href="%s" target="_blank" rel="noopener noreferrer">Ver archivo: %s</a></p>'
    #             ) % (download_path, display_name)
    #         )
    #     return markupsafe.Markup('').join(links)
