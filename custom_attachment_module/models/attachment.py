# from odoo import models, fields, api
# import base64
# import requests
# import logging
# import hashlib
# import random
# import json
#
# _logger = logging.getLogger(__name__)
#
# class Attachment(models.Model):
#     _inherit = 'ir.attachment'
#
#     hash_value = fields.Char('Hash', readonly=True)
#     external_url = fields.Char('External URL', readonly=True)
#
#     @api.model
#     def create(self, vals):
#         _logger.info("Método create de Attachment ejecutado.")
#
#         filename = vals.get('name', 'archivo')  # Obtener el nombre del archivo si está disponible
#
#         if 'datas' in vals:
#             try:
#                 base64_encoded = vals['datas']  # Sin decodificar
#
#                 random_hash = hashlib.sha256(str(random.getrandbits(256)).encode('utf-8')).hexdigest()
#                 _logger.info(f"Hash generado aleatoriamente: {random_hash}")
#
#                 bytes_data = {
#                     "foto": base64_encoded
#                 }
#                 json_data = json.dumps(bytes_data)
#
#                 full_url = f'https://apinf.incomel.com.gt/fotografia/{random_hash}'
#                 _logger.info(f"URL completa: {full_url}")
#
#                 _logger.info(f"Datos enviados al API: {json_data}")
#
#                 response = requests.post(
#                     full_url,
#                     data=json_data,
#                     headers={'Content-Type': 'application/json'},
#                     timeout=30,
#                     verify=False
#                 )
#
#                 _logger.info(f"API Response: {response.status_code} - {response.text}")
#                 if response.status_code == 200:
#                     response_json = response.json()
#                     if response_json.get("success"):
#                         vals['hash_value'] = random_hash
#                         vals['external_url'] = full_url
#                     else:
#                         _logger.error(f"Error en la respuesta del API: {response_json}")
#                 else:
#                     _logger.error(f"Error al llamar al API: {response.status_code} - {response.text}")
#
#             except requests.exceptions.RequestException as e:
#                 _logger.error(f"Excepción de solicitud HTTP: {str(e)}")
#             except Exception as e:
#                 _logger.error(f"Excepción general: {str(e)}")
#
#             vals.pop('datas', None)
#
#         else:
#             _logger.error("El campo 'datas' no está disponible en los valores proporcionados.")
#
#         # Crear el registro sin el campo 'datas'
#         record = super(Attachment, self).create(vals)
#
#         return record
# from odoo import models, fields, api
# import requests
# import logging
# import base64
# import hashlib
# from odoo.exceptions import UserError
# import time
# import random
#
# _logger = logging.getLogger(__name__)
#
# # Define the constants for Backblaze credentials and bucket name
# BACKBLAZE_ACCOUNT_ID = "005180a072ea17e0000000002"
# BACKBLAZE_APPLICATION_KEY = "K005DjywVAK5HRLAi4sRDNGwdY9Bcvc"
# BACKBLAZE_BUCKET_ID = "3158d00a30d702be9a21071e"
# DocumentsOdooInc = 'DocumentsOdooInc'
#
# MAX_RETRIES = 5
# INITIAL_RETRY_DELAY = 1  # seconds
#
#
# class BackblazeAttachment(models.Model):
#     _inherit = 'ir.attachment'
#
#     hash_value = fields.Char('Hash', readonly=True)
#     external_url = fields.Char('External URL', readonly=True)
#     upload_error = fields.Text('Upload Error', readonly=True)
#     use_backblaze = fields.Boolean('Use Backblaze', default=True)
#
#     def encode_file_name(self, file_name):
#         return base64.b64encode(file_name.encode('utf-8')).decode('utf-8')
#
#     @api.model
#     def get_backblaze_enabled(self):
#         return self.env['ir.config_parameter'].sudo().get_param('backblaze_attachment.enabled',
#                                                                 'True').lower() == 'true'
#
#     def authorize_account(self):
#         """ Authenticate the Backblaze account using hardcoded credentials """
#         _logger.info("Starting account authorization with Backblaze")
#
#         try:
#             response = requests.get(
#                 'https://api.backblazeb2.com/b2api/v2/b2_authorize_account',
#                 auth=(BACKBLAZE_ACCOUNT_ID, BACKBLAZE_APPLICATION_KEY),
#                 timeout=30
#             )
#             response.raise_for_status()
#             _logger.info("Successfully authorized with Backblaze")
#             return response.json()
#         except requests.exceptions.RequestException as e:
#             _logger.error(f"Failed to authorize Backblaze account. Error: {str(e)}")
#             raise UserError(f"Failed to authorize Backblaze account. Error: {str(e)}")
#
#     def get_upload_url(self):
#         """ Obtain the upload URL for Backblaze """
#         _logger.info("Requesting upload URL from Backblaze")
#         auth_data = self.authorize_account()
#         url = f"{auth_data['apiUrl']}/b2api/v2/b2_get_upload_url"
#         headers = {'Authorization': auth_data['authorizationToken']}
#         data = {'bucketId': BACKBLAZE_BUCKET_ID}
#
#         try:
#             response = requests.post(url, headers=headers, json=data, timeout=30)
#             response.raise_for_status()
#             _logger.info("Upload URL obtained successfully")
#             return response.json()
#         except requests.exceptions.RequestException as e:
#             _logger.error(f"Failed to get upload URL. Error: {str(e)}")
#             raise UserError(f"Failed to get upload URL. Error: {str(e)}")
#
#     def upload_file(self, upload_url, upload_auth_token, file_data, file_name):
#         """ Upload a file to Backblaze """
#         encoded_file_name = self.encode_file_name(file_name)
#         _logger.info(f"Uploading file: {file_name} (encoded: {encoded_file_name})")
#         headers = {
#             'Authorization': upload_auth_token,
#             'X-Bz-File-Name': encoded_file_name,
#             'Content-Type': 'b2/x-auto',
#             'X-Bz-Content-Sha1': 'do_not_verify'
#         }
#
#         try:
#             response = requests.post(upload_url, headers=headers, data=file_data, timeout=30)
#             response.raise_for_status()
#             _logger.info(f"File uploaded successfully: {file_name}")
#             return response.json()
#         except requests.exceptions.RequestException as e:
#             _logger.error(f"Failed to upload file. Error: {str(e)}")
#             if hasattr(e, 'response') and e.response is not None:
#                 _logger.error(f"Response status code: {e.response.status_code}")
#                 _logger.error(f"Response content: {e.response.text}")
#             raise UserError(f"Failed to upload file to Backblaze. Error: {str(e)}")
#
#     def get_download_url(self, file_name, for_preview=False):
#         """ Obtain the download URL for a file from Backblaze """
#         encoded_file_name = self.encode_file_name(file_name)
#         _logger.info(f"Requesting download authorization for file: {file_name} (encoded: {encoded_file_name})")
#         auth_data = self.authorize_account()
#
#         url = f"{auth_data['apiUrl']}/b2api/v2/b2_get_download_authorization"
#         headers = {'Authorization': auth_data['authorizationToken']}
#         data = {
#             'bucketId': BACKBLAZE_BUCKET_ID,
#             'fileNamePrefix': encoded_file_name,
#             'validDurationInSeconds': 3600
#         }
#
#         try:
#             response = requests.post(url, headers=headers, json=data, timeout=30)
#             response.raise_for_status()
#             download_auth = response.json()
#             download_url = f"{auth_data['downloadUrl']}/file/{DocumentsOdooInc}/{encoded_file_name}?Authorization={download_auth['authorizationToken']}"
#             if for_preview:
#                 download_url += "&response-content-disposition=inline"
#             _logger.info(f"Download URL obtained successfully: {download_url}")
#             return download_url
#         except requests.exceptions.RequestException as e:
#             _logger.error(f"Failed to get download URL. Error: {str(e)}")
#             if hasattr(e, 'response') and e.response is not None:
#                 _logger.error(f"Response status code: {e.response.status_code}")
#                 _logger.error(f"Response content: {e.response.text}")
#             raise UserError(f"Failed to get download URL. Error: {str(e)}")
#
#     def check_file_exists(self, file_name):
#         auth_data = self.authorize_account()
#         url = f"{auth_data['apiUrl']}/b2api/v2/b2_download_file_by_name"
#         headers = {'Authorization': auth_data['authorizationToken']}
#
#         file_names_to_check = [
#             file_name,
#             self.encode_file_name(file_name)
#         ]
#
#         for name in file_names_to_check:
#             params = {
#                 'bucketName': DocumentsOdooInc,
#                 'fileName': name
#             }
#             try:
#                 response = requests.head(url, headers=headers, params=params, timeout=10)
#                 _logger.info(f"File existence check for {name}: Status {response.status_code}")
#                 if response.status_code == 200:
#                     return True
#             except requests.exceptions.RequestException as e:
#                 _logger.error(f"Error checking file existence for {name}: {str(e)}")
#
#         _logger.error(f"File not found: {file_name}")
#         return False
#
#     def upload_to_backblaze(self, file_data, file_name):
#         if not self.get_backblaze_enabled():
#             return False, "Backblaze uploads are currently disabled."
#
#         for attempt in range(MAX_RETRIES):
#             try:
#                 upload_data = self.get_upload_url()
#                 upload_result = self.upload_file(upload_data['uploadUrl'], upload_data['authorizationToken'], file_data,
#                                                  file_name)
#                 external_url = self.get_download_url(file_name)
#                 return external_url, None
#             except Exception as e:
#                 delay = (2 ** attempt + random.uniform(0, 1)) * INITIAL_RETRY_DELAY
#                 _logger.warning(
#                     f"Backblaze upload failed (attempt {attempt + 1}). Retrying in {delay:.2f} seconds. Error: {str(e)}")
#                 time.sleep(delay)
#
#         return False, f"Failed to upload to Backblaze after {MAX_RETRIES} attempts."
#
#     @api.model_create_multi
#     def create(self, vals_list):
#         for vals in vals_list:
#             if 'datas' in vals and vals.get('use_backblaze', True) and self.get_backblaze_enabled():
#                 file_data = base64.b64decode(vals['datas'])
#                 hash_object = hashlib.sha256(file_data)
#                 vals['hash_value'] = hash_object.hexdigest()
#
#                 external_url, error = self.upload_to_backblaze(file_data, vals.get('name', 'archivo'))
#                 if external_url:
#                     vals['external_url'] = external_url
#                     vals['upload_error'] = False
#                 else:
#                     vals['upload_error'] = error
#                     _logger.error(f"Backblaze upload failed: {error}")
#
#         return super(BackblazeAttachment, self).create(vals_list)
#
#     def write(self, vals):
#         if 'datas' in vals and self.use_backblaze and self.get_backblaze_enabled():
#             file_data = base64.b64decode(vals['datas'])
#             hash_object = hashlib.sha256(file_data)
#             vals['hash_value'] = hash_object.hexdigest()
#
#             file_name = vals.get('name', self.name or 'archivo')
#             external_url, error = self.upload_to_backblaze(file_data, file_name)
#             if external_url:
#                 vals['external_url'] = external_url
#                 vals['upload_error'] = False
#             else:
#                 vals['upload_error'] = error
#                 _logger.error(f"Backblaze upload failed: {error}")
#
#         result = super(BackblazeAttachment, self).write(vals)
#
#         # Update external_url after write if it's not already updated
#         if 'datas' in vals and 'external_url' not in vals:
#             for record in self:
#                 try:
#                     fresh_url = record.get_download_url(record.name)
#                     record.external_url = fresh_url
#                 except Exception as e:
#                     _logger.error(f"Failed to update external URL for {record.name}: {str(e)}")
#
#         return result
#
#     def action_preview_file(self):
#         self.ensure_one()
#         if not self.external_url:
#             raise UserError("No external URL found for this file.")
#
#         _logger.info(f"Attempting to preview file: {self.name}")
#
#         if not self.check_file_exists(self.name):
#             _logger.error(f"File not found in Backblaze: {self.name}")
#             raise UserError(
#                 f"File '{self.name}' not found in Backblaze. It may have been deleted or not properly uploaded. Please check the Odoo logs for more details.")
#
#         try:
#             fresh_url = self.get_download_url(self.name, for_preview=True)
#             self.external_url = fresh_url
#             _logger.info(f"Preview URL refreshed: {fresh_url}")
#         except Exception as e:
#             _logger.error(f"Failed to refresh download URL for {self.name}: {str(e)}")
#             raise UserError(f"Failed to generate preview URL for '{self.name}'. Error: {str(e)}")
#
#         return {
#             'type': 'ir.actions.act_url',
#             'url': self.external_url,
#             'target': 'new'
#         }
#
#     def action_download_file(self):
#         """ Method executed when clicking the 'Download File' button """
#         self.ensure_one()
#         _logger.info(f"Initiating file download: {self.external_url}")
#         if not self.external_url:
#             raise UserError("No external URL found for this file.")
#
#         return {
#             'type': 'ir.actions.act_url',
#             'url': f'/web/content/?model=ir.attachment&id={self.id}&filename_field=name&field=datas&download=true&filename={self.name}',
#             'target': 'self',
#         }
#
#     def list_files_in_bucket(self):
#         auth_data = self.authorize_account()
#         url = f"{auth_data['apiUrl']}/b2api/v2/b2_list_file_names"
#         headers = {'Authorization': auth_data['authorizationToken']}
#         data = {
#             'bucketId': BACKBLAZE_BUCKET_ID,
#             'maxFileCount': 1000  # Adjust as needed
#         }
#
#         try:
#             response = requests.post(url, headers=headers, json=data, timeout=30)
#             response.raise_for_status()
#             files = response.json().get('files', [])
#             _logger.info(f"Files in bucket: {[f['fileName'] for f in files]}")
#             return files
#         except requests.exceptions.RequestException as e:
#             _logger.error(f"Failed to list files in bucket: {str(e)}")
#             return []
#
#     def diagnose_file_issues(self):
#         _logger.info(f"Diagnosing issues for file: {self.name}")
#         _logger.info(f"Current external URL: {self.external_url}")
#
#         bucket_files = self.list_files_in_bucket()
#         file_in_bucket = any(f['fileName'] == self.name for f in bucket_files)
#
#         if file_in_bucket:
#             _logger.info(f"File '{self.name}' found in Backblaze bucket.")
#         else:
#             _logger.error(f"File '{self.name}' NOT found in Backblaze bucket.")
#             similar_files = [f['fileName'] for f in bucket_files if self.name in f['fileName']]
#             if similar_files:
#                 _logger.info(f"Similar files found: {similar_files}")
#
#         # Check if the file exists locally
#         if self.datas:
#             _logger.info(f"File '{self.name}' exists locally in Odoo.")
#         else:
#             _logger.error(f"File '{self.name}' does not exist locally in Odoo.")
#
#         # Try to get a fresh download URL
#         try:
#             fresh_url = self.get_download_url(self.name)
#             _logger.info(f"Fresh download URL generated: {fresh_url}")
#         except Exception as e:
#             _logger.error(f"Failed to generate fresh download URL: {str(e)}")
#
#         return {
#             'type': 'ir.actions.client',
#             'tag': 'display_notification',
#             'params': {
#                 'title': 'File Diagnosis Complete',
#                 'message': 'Check Odoo logs for detailed diagnostic information.',
#                 'sticky': False,
#             }
#         }

from fileinput import filename
import os
import re
import unicodedata
from odoo import models, fields, api
import requests
import logging
import base64
import hashlib
from odoo.exceptions import UserError
import time
import random
from datetime import datetime
import io
from odoo.http import request
import markupsafe


_logger = logging.getLogger(__name__)

# Define the constants for Backblaze credentials and bucket name
BACKBLAZE_ACCOUNT_ID = "005180a072ea17e0000000002"
BACKBLAZE_APPLICATION_KEY = "K005DjywVAK5HRLAi4sRDNGwdY9Bcvc"
BACKBLAZE_BUCKET_ID = "3158d00a30d702be9a21071e"
DocumentsOdooInc = 'DocumentsOdooInc'

MAX_RETRIES = 5
INITIAL_RETRY_DELAY = 1  # seconds


class BackblazeAttachment(models.Model):
    _inherit = 'ir.attachment'

    # _EXTENSION_RESTRICTED_MODELS = {
    #     'sale.order',
    #     'project.task',
    #     'helpdesk.ticket',
    # }

    hash_value = fields.Char('Hash', readonly=True)
    external_url = fields.Char('External URL', readonly=True)
    upload_error = fields.Text('Upload Error', readonly=True)
    use_backblaze = fields.Boolean('Use Backblaze', default=True)
    original_name = fields.Char('Original File Name')
    view_extrenal_url_text = fields.Text('External', compute='_compute_view_external_url')

    def _compute_view_external_url(self):
        for record in self:
            # if record.external_url:
            #     record.view_extrenal_url_text = self.get_download_url(record.name,for_preview=False)
            # else:
            #     record.view_extrenal_url_text = 'No disponible'

            record.view_extrenal_url_text = 'No disponible'

    # def edit_text(self, texto):
    #     reemplazos = {
    #     'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
    #     'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
    #     'ñ': 'n', 'Ñ': 'N',
    #     'ü': 'u', 'Ü': 'U'
    #     }
    #     # Reemplazar caracteres especiales
    #     for original, reemplazo in reemplazos.items():
    #         texto = texto.replace(original, reemplazo)
    #     # Reemplazar espacios por guiones bajos
    #     texto = texto.replace(" ", "_")
        
    #     return texto

    # def _sanitize_file_name_part(self, text):
    #     """Deja solo letras y numeros (ASCII); cualquier otro caracter pasa a '_'."""
    #     text = unicodedata.normalize('NFKD', str(text or ''))
    #     text = text.encode('ascii', 'ignore').decode('ascii')
    #     text = re.sub(r'[^A-Za-z0-9]+', '_', text)
    #     return text.strip('_')

    # def _sanitize_full_name(self, file_name):
    #     """Sanitiza un nombre completo (base + extension) a solo letras y numeros."""
    #     base, ext = os.path.splitext(str(file_name or ''))
    #     base = self._sanitize_file_name_part(base) or 'archivo'
    #     ext = re.sub(r'[^A-Za-z0-9]', '', unicodedata.normalize('NFKD', ext).encode('ascii', 'ignore').decode('ascii'))
    #     return f"{base}.{ext}" if ext else base

    # def get_last_attachment_id(self):
    #     """Return the ID of the last created attachment"""
    #     last_attachment = self.search([], order='id desc', limit=1)
    #     return last_attachment.id if last_attachment else None

    # def encode_file_name(self, file_name):
    #     return base64.b64encode(file_name.encode('utf-8')).decode('utf-8')

    # @api.model
    # def get_allowed_extensions(self):
    #     allowed_ext = self.env['ir.config_parameter'].sudo().get_param(
    #         'custom_attachment.allowed_extensions', ''
    #     )
    #     if allowed_ext:
    #         extensions = [ext.strip().lower() for ext in allowed_ext.split(',') if ext.strip()]
    #         return extensions
    #     return []

    # def _validate_file_extension(self, file_name):
    #     allowed_extensions = self.get_allowed_extensions()
    #     if not allowed_extensions:
    #         return True
        
    #     if file_name:
    #         file_ext = os.path.splitext(file_name)[1].lower()
    #         if file_ext not in allowed_extensions:
    #             raise UserError(
    #                 f'La extensión del archivo "{file_name}" ({file_ext}) no está permitida.\n'
    #                 f'Extensiones permitidas: {", ".join(allowed_extensions)}'
    #             )
    #     return True

    # def _should_validate_extension(self, vals=None, record=None):
    #     model_name = False
    #     if vals:
    #         model_name = vals.get('res_model')
    #     if not model_name and record:
    #         model_name = record.res_model
    #     if not model_name:
    #         model_name = self._context.get('active_model')
    #     if not model_name:
    #         return False
    #     config_param = self.env['ir.config_parameter'].sudo()
    #     # get_param devuelve False si el parametro no existe, y el string si existe.
    #     # Si no existe (False), usar los modelos historicos por defecto.
    #     # Si existe pero esta vacio (''), el usuario lo guardo vacio a proposito: no aplicar restriccion.
    #     stored = config_param.get_param('custom_attachment.restricted_models')
    #     if stored is False or stored is None:
    #         stored = 'sale.order,project.task,helpdesk.ticket'
    #     restricted_set = {m.strip() for m in stored.split(',') if m.strip()}
    #     return model_name in restricted_set

    # @api.model
    # def get_backblaze_enabled(self):
    #     return self.env['ir.config_parameter'].sudo().get_param('backblaze_attachment.enabled',
    #                                                             'True').lower() == 'true'

    # def generate_file_name(self,file_name=None):
    #     now = datetime.now()
    #     user_code = self.env.user.id


    #     user_name = self._sanitize_file_name_part(self.env.user.name) or 'unknown'
    #     last_id = self.get_last_attachment_id() or 0

    #     if 'active_model' in self._context and 'active_id' in self._context:
    #         name_model = self.env[self._context['active_model']].browse(self._context['active_id']).name
    #         if not name_model:
    #             name_model = self.env[self._context['active_model']].browse(self._context['active_id']).display_name or 'unknown'
    #     else:
    #         name_model = 'unknown'
    #     if self._context.get('active_model') == 'project.task':
    #         task_id = self.env['project.task'].browse(self._context['active_id'])
    #         if task_id and task_id.x_studio_pedido:
    #             name_model = task_id.x_studio_pedido.name
    #         else:
    #             name_model = task_id.name or 'unknown'
    #         # name_model = self.env['project.task'].browse(self._context['active_id']).x_studio_pedido.name
    #     name_model = self._sanitize_file_name_part(name_model) or 'unknown'

    #     base_name = f"{str(last_id + 1)}_{name_model}_{user_name}_{now.strftime('%Y%m%d_%H%M%S')}"
    #     # base_name = f"odoo_{now.strftime('%Y%m%d')}_{user_code}_{now.strftime('%H%M%S')}"
    #     base_name = self._sanitize_file_name_part(base_name) or 'archivo'

    #     # Get the file extension from the original name if available (solo letras y numeros)
    #     if file_name and '.' in file_name:
    #         file_extension = re.sub(r'[^A-Za-z0-9]', '', unicodedata.normalize(
    #             'NFKD', os.path.splitext(file_name)[1]).encode('ascii', 'ignore').decode('ascii'))
    #         if file_extension:
    #             return f"{base_name}.{file_extension}"

    #     return base_name

    # def authorize_account(self):
    #     """ Authenticate the Backblaze account using hardcoded credentials """
    #     _logger.info("Starting account authorization with Backblaze")

    #     try:
    #         response = requests.get(
    #             'https://api.backblazeb2.com/b2api/v2/b2_authorize_account',
    #             auth=(BACKBLAZE_ACCOUNT_ID, BACKBLAZE_APPLICATION_KEY),
    #             timeout=30
    #         )
    #         response.raise_for_status()
    #         _logger.info("Successfully authorized with Backblaze")
    #         return response.json()
    #     except requests.exceptions.RequestException as e:
    #         _logger.error(f"Failed to authorize Backblaze account. Error: {str(e)}")
    #         raise UserError(f"Failed to authorize Backblaze account. Error: {str(e)}")

    # def get_upload_url(self):
    #     """ Obtain the upload URL for Backblaze """
    #     _logger.info("Requesting upload URL from Backblaze")
    #     auth_data = self.authorize_account()
    #     url = f"{auth_data['apiUrl']}/b2api/v2/b2_get_upload_url"
    #     headers = {'Authorization': auth_data['authorizationToken']}
    #     data = {'bucketId': BACKBLAZE_BUCKET_ID}

    #     try:
    #         response = requests.post(url, headers=headers, json=data, timeout=30)
    #         response.raise_for_status()
    #         _logger.info("Upload URL obtained successfully")
    #         return response.json()
    #     except requests.exceptions.RequestException as e:
    #         _logger.error(f"Failed to get upload URL. Error: {str(e)}")
    #         raise UserError(f"Failed to get upload URL. Error: {str(e)}")

    # def upload_file(self, upload_url, upload_auth_token, file_data, file_name):
    #     """ Upload a file to Backblaze """
    #     # encoded_file_name = self.encode_file_name(file_name)
    #     encoded_file_name = file_name
    #     _logger.info(f"Uploading file: {file_name} (encoded: {encoded_file_name})")
    #     headers = {
    #         'Authorization': upload_auth_token,
    #         'X-Bz-File-Name': encoded_file_name,
    #         'Content-Type': 'b2/x-auto',
    #         'X-Bz-Content-Sha1': 'do_not_verify'
    #     }
    #     try:
    #         response = requests.post(upload_url, headers=headers, data=file_data, timeout=30)
    #         response.raise_for_status()
    #         _logger.info(f"File uploaded successfully: {file_name}")
    #         return response.json()
    #     except requests.exceptions.RequestException as e:
    #         _logger.error(f"Failed to upload file. Error: {str(e)}")
    #         raise UserError(f"Failed to upload file to Backblaze. Error: {str(e)}")

    # def get_download_url(self, file_name, for_preview=False):
    #     """ Obtain the download URL for a file from Backblaze """
    #     # encoded_file_name = self.encode_file_name(file_name)
    #     encoded_file_name = file_name
    #     _logger.info(f"Requesting download authorization for file: {file_name} (encoded: {encoded_file_name})")
    #     auth_data = self.authorize_account()

    #     url = f"{auth_data['apiUrl']}/b2api/v2/b2_get_download_authorization"
    #     headers = {'Authorization': auth_data['authorizationToken']}
    #     data = {
    #         'bucketId': BACKBLAZE_BUCKET_ID,
    #         'fileNamePrefix': encoded_file_name,
    #         'validDurationInSeconds': 604800
    #     }
    #     try:
    #         response = requests.post(url, headers=headers, json=data, timeout=30)
    #         response.raise_for_status()
    #         download_auth = response.json()
    #         download_url = f"{auth_data['downloadUrl']}/file/{DocumentsOdooInc}/{encoded_file_name}?Authorization={download_auth['authorizationToken']}"
    #         if for_preview:
    #             download_url += "&response-content-disposition=inline"
    #         _logger.info(f"Download URL obtained successfully: {download_url}")
    #         return download_url
    #     except requests.exceptions.RequestException as e:
    #         _logger.error(f"Failed to get download URL. Error: {str(e)}")
    #         raise UserError(f"Failed to get download URL. Error: {str(e)}")

    # def upload_to_backblaze(self, file_data, file_name):
    #     if not self.get_backblaze_enabled():
    #         return False, "Backblaze uploads are currently disabled."
    #     for attempt in range(MAX_RETRIES):
    #         try:
    #             upload_data = self.get_upload_url()
    #             upload_result = self.upload_file(upload_data['uploadUrl'], upload_data['authorizationToken'], file_data, file_name)
    #             external_url = self.get_download_url(file_name)
    #             _logger.info(f"File uploaded successfully. External URL: {external_url}")
    #             return external_url, None
    #         except Exception as e:
    #             delay = (2 ** attempt + random.uniform(0, 1)) * INITIAL_RETRY_DELAY
    #             _logger.warning(f"Backblaze upload failed (attempt {attempt + 1}). Retrying in {delay:.2f} seconds. Error: {str(e)}")
    #             time.sleep(delay)
    #     return False, f"Failed to upload to Backblaze after {MAX_RETRIES} attempts."

    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         if 'name' in vals:
    #             vals['original_name'] = vals['name']
    #             if self._should_validate_extension(vals=vals):
    #                 self._validate_file_extension(vals['name'])

    #         new_file_name = self.generate_file_name(vals.get('name'))

    #         # Excluir assets de Backblaze. Si el attachment es un asset bundle
    #         # (res_model = 'ir.ui.view' o tiene url de asset), el archivo debe
    #         # quedarse en el filestore local porque Odoo lo sirve via /web/assets.
    #         is_asset_bundle = (
    #             vals.get('res_model') == 'ir.ui.view'
    #             or vals.get('public')
    #             or (vals.get('url') and isinstance(vals.get('url'), str) and '/web/assets' in vals.get('url', ''))
    #         )

    #         if ('datas' in vals or 'raw' in vals) and vals.get('use_backblaze', True) and self.get_backblaze_enabled() and not is_asset_bundle:
    #             if 'datas' in vals:
    #                 file_data = base64.b64decode(vals['datas'])
    #             else:
    #                 file_data = vals['raw']

    #             hash_object = hashlib.sha256(file_data)
    #             vals['hash_value'] = hash_object.hexdigest()

    #             external_url, error = self.upload_to_backblaze(file_data, new_file_name)
    #             if external_url:
    #                 vals['external_url'] = external_url
    #                 vals['upload_error'] = False
    #                 vals.pop('datas', None)
    #                 vals.pop('raw', None)
    #             else:
    #                 vals['upload_error'] = error
    #                 _logger.error(f"Backblaze upload failed: {error}")

    #         vals['name'] = new_file_name

    #     records = super(BackblazeAttachment, self).create(vals_list)

    #     for record, vals in zip(records, vals_list):
    #         if record.external_url and record.res_model and record.res_id:
    #             try:
    #                 target = self.env[record.res_model].sudo().browse(record.res_id)
    #                 if hasattr(target, 'message_post'):
    #                     display_name = record.original_name or record.name or 'archivo'
    #                     # Link al controlador del modulo en vez de la URL firmada
    #                     # de Backblaze. La URL firmada caduca a los 7 dias
    #                     # (validDurationInSeconds=604800 en get_download_url),
    #                     # pero el controlador genera una URL fresca en cada
    #                     # click y redirige, asi el link del chatter no expira.
    #                     download_path = f'/web/content/backblaze_download/{record.id}'
    #                     link_body = markupsafe.Markup(
    #                         f'<p><a href="{download_path}" target="_blank">'
    #                         f'\U0001F4C4 Ver archivo: {display_name}</a></p>'
    #                     )
    #                     target.message_post(body=link_body)
    #             except Exception as e:
    #                 _logger.error(f"Failed to post Backblaze link in chatter for {record.res_model},{record.res_id}: {e}")

    #     return records

    # def write(self, vals):
    #     # Cada registro necesita su propio nombre/subida: procesar uno a uno.
    #     if len(self) > 1 and ({'datas', 'raw', 'name'} & set(vals)):
    #         for record in self:
    #             record.write(dict(vals))
    #         return True

    #     if 'name' in vals:
    #         for record in self:
    #             if record._should_validate_extension(vals=vals, record=record):
    #                 record._validate_file_extension(vals['name'])

    #     is_asset_bundle = any(
    #         record.res_model == 'ir.ui.view' or record.public or (record.url and '/web/assets' in (record.url or ''))
    #         for record in self
    #     ) if self else False

    #     has_content = 'datas' in vals or 'raw' in vals

    #     # Renombrar un archivo ya subido no lo renombra en Backblaze (el nombre es la clave del archivo):
    #     # se conserva el name actual para que el link de descarga siga funcionando.
    #     if 'name' in vals and not has_content and self.external_url:
    #         _logger.info(f"Se ignora el cambio de nombre del adjunto {self.id}: el archivo esta en Backblaze")
    #         vals = {key: value for key, value in vals.items() if key != 'name'}

    #     if has_content and self.use_backblaze and self.get_backblaze_enabled() and not is_asset_bundle:
    #         if 'datas' in vals:
    #             file_data = base64.b64decode(vals['datas'])
    #         else:
    #             file_data = vals['raw']

    #         hash_object = hashlib.sha256(file_data)
    #         vals['hash_value'] = hash_object.hexdigest()

    #         # El nombre en Backblaze debe ser igual al name guardado en Odoo (asi se genera la URL de descarga)
    #         file_name = self._sanitize_full_name(vals.get('name') or self.name)
    #         if 'name' in vals:
    #             vals['name'] = file_name

    #         external_url, error = self.upload_to_backblaze(file_data, file_name)
    #         if external_url:
    #             vals['external_url'] = external_url
    #             vals['upload_error'] = False
    #             vals.pop('datas', None)
    #             vals.pop('raw', None)
    #         else:
    #             vals['upload_error'] = error
    #             _logger.error(f"Backblaze upload failed: {error}")

    #     return super(BackblazeAttachment, self).write(vals)

    # def action_download_file(self):
    #     if not self.name:
    #         raise UserError("No se encontró el nombre del archivo.")

    #     # Generar la URL temporal en el momento de la descarga
    #     download_url = self.get_download_url(
    #         self.name,
    #         for_preview=False
    #     )
    #     self.view_extrenal_url_text = download_url
    #     return {
    #         'type': 'ir.actions.act_url',
    #         'url': download_url,
    #         'target': 'new',
    #     }

    
