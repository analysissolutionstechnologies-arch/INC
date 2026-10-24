import base64
import mimetypes
import os
from urllib.parse import unquote, urlparse
from odoo import http
from odoo.exceptions import UserError
from odoo.http import request, content_disposition, route
from odoo.addons.mail.controllers.attachment import AttachmentController
from odoo.addons.mail.models.discuss.mail_guest import add_guest_to_context
import logging

_logger = logging.getLogger(__name__)


class BackblazeDownloadController(http.Controller):

    @http.route('/web/content/backblaze_download/<int:attachment_id>', type='http', auth='public')
    def download_backblaze_file(self, attachment_id, **kw):
        attachment = request.env['ir.attachment'].sudo().browse(attachment_id)
        if not attachment.exists():
            _logger.error(f"Attachment with id {attachment_id} not found")
            return request.not_found()

        try:
            _logger.info(f"Preparing download for attachment: {attachment.name}")

            file_name = attachment.name

            # Determine the correct file extension and MIME type
            original_ext = os.path.splitext(attachment.original_name or '')[1]
            mime_type = attachment.mimetype or mimetypes.guess_type(attachment.original_name or '')[0] or 'application/octet-stream'

            # If the new name doesn't have an extension, add the original extension
            if not os.path.splitext(file_name)[1] and original_ext:
                file_name += original_ext

            # Si el archivo está en Backblaze (external_url presente), redirigir a la URL temporal
            if attachment.external_url:
                _logger.info(f"Redirecting to Backblaze download URL for attachment: {attachment.name}")
                remote_file_name = attachment.name
                remote_path = unquote(urlparse(attachment.external_url).path)
                bucket_prefix = '/file/DocumentsOdooInc/'
                if bucket_prefix in remote_path:
                    remote_file_name = remote_path.split(bucket_prefix, 1)[1]
                download_url = attachment.get_download_url(remote_file_name, for_preview=True)
                return request.redirect(download_url, local=False)

            # Fallback: intentar servir desde la BD si todavía tiene contenido local (datas)
            file_content = attachment.datas
            if not file_content:
                _logger.error(f"No content found for attachment: {attachment.name} (not in Backblaze nor in DB)")
                return request.not_found()

            # Decode the Base64 content
            decoded_content = base64.b64decode(file_content)

            _logger.info(f"Serving file from DB: {file_name}, Size: {len(decoded_content)} bytes, Type: {mime_type}")

            headers = [
                ('Content-Type', mime_type),
                ('Content-Disposition', content_disposition(file_name)),
                ('Content-Length', str(len(decoded_content))),
            ]

            response = request.make_response(decoded_content, headers=headers)
            return response

        except Exception as e:
            _logger.error(f"Failed to prepare file for download: {str(e)}", exc_info=True)
            return request.not_found()


class CustomAttachmentController(AttachmentController):
    """Extiende el controlador de subida de adjuntos del chatter.

    El chatter marca los adjuntos pendientes con ``res_model='mail.compose.message'``
    hasta que el mensaje se envia. Como ese modelo no esta en
    ``custom_attachment.restricted_models``, ``_should_validate_extension``
    omite la validacion y los archivos con extension no permitida se suben
    a Backblaze, dejando el spinner del chatter en estado de carga durante
    los reintentos de subida.

    Este override valida la extension con ``thread_model`` (el modelo real
    del hilo, p. ej. ``project.task``) antes de delegar al flujo estandar.
    Si la extension no esta permitida, se devuelve ``{"error": ...}`` como
    JSON para que el cliente JS del chatter lo muestre como notificacion,
    consistente con el resto de errores de subida del chatter.
    """

    @route()
    @add_guest_to_context
    def mail_attachment_upload(self, ufile, thread_id, thread_model, is_pending=False, **kwargs):
        # thread_model es el modelo real del hilo (p. ej. project.task), a
        # diferencia de res_model que el chatter sobrescribe con
        # 'mail.compose.message' mientras el mensaje esta pendiente.
        attachment_env = request.env["ir.attachment"].sudo()
        if attachment_env._should_validate_extension(vals={"res_model": thread_model}):
            try:
                attachment_env._validate_file_extension(ufile.filename)
            except UserError as e:
                # Respuesta JSON esperada por el cliente JS del chatter
                # (attachment_upload_service): la clave 'error' se muestra
                # como notificacion de danger.
                return request.make_json_response({"error": str(e)})
        # Pasar thread_model/thread_id al contexto para que generate_file_name
        # (attachment.py:517) pueda resolver el nombre del registro real en
        # vez de caer en 'unknown'. El chatter sobrescribe res_model con
        # 'mail.compose.message' (is_pending), pero el contexto preserva el
        # modelo real del hilo. El thread ya fue validado por el controlador
        # padre (mail/controllers/attachment.py:50-52) que levanta NotFound
        # si no existe.
        request.update_context(active_model=thread_model, active_id=int(thread_id))
        return super().mail_attachment_upload(ufile, thread_id, thread_model, is_pending, **kwargs)
