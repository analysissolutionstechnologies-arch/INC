# controllers/main.py
from odoo import http
from odoo.http import request
import random
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class HelpdeskTokenController(http.Controller):

    # -------------------------------------------------------------------------
    # 1. ENVIAR TOKEN (Crea registro, pone vencimiento +5min, envia correo)
    # -------------------------------------------------------------------------
    @http.route('/helpdesk/enviar_token', type='json', auth="public", website=True, csrf=False)
    def enviar_token_agencia(self, email, agencia):
        if not email:
            return {'success': False, 'error': 'No hay correo configurado.'}

        try:
            # Generar datos
            token = str(random.randint(100000, 999999))
            vencimiento = datetime.now() + timedelta(minutes=5)

            # Crear registro en el modelo
            # x_studio_validado es False por defecto en Odoo si es booleano
            request.env['x_tokens_sinergia_bda'].sudo().create({
                'x_name': token,
                'x_studio_nombre_agencia': agencia,
                'x_studio_vencimiento': vencimiento,
                'x_studio_validado': False 
            })

            # Enviar Correo
            subject = f"Codigo de Seguridad - {agencia}"
            body_html = f"""
                <div style="font-family: sans-serif; padding: 20px;">
                    <div style="background-color: #f8f9fa; padding: 20px; border: 1px solid #ddd;">
                        <h2 style="color: #28a745;">Codigo de Validacion</h2>
                        <p>Agencia solicitada: <strong>{agencia}</strong></p>
                        <h1 style="background:#fff; padding:10px; display:inline-block;">{token}</h1>
                        <p style="color: #dc3545; font-size: 14px;">Este codigo expira en 5 minutos.</p>
                    </div>
                </div>
            """
            
            
            mail_values = {
                'subject': subject,
                'body_html': body_html,
                'email_to': email,
                'email_from': request.env.user.company_id.email or 'noreply@tuempresa.com',
                'auto_delete': False,
            }
            request.env['mail.mail'].sudo().create(mail_values).send()

            return {'success': True}

        except Exception as e:
            _logger.error(f"Error enviando token: {str(e)}")
            return {'success': False, 'error': str(e)}

    # -------------------------------------------------------------------------
    # 2. VALIDAR TOKEN (Revisa vencimiento y marca Validado = True)
    # -------------------------------------------------------------------------
   
   
    @http.route('/helpdesk/validar_token', type='json', auth="public", website=True, csrf=False)
    def validar_token_agencia(self, token, agencia):
        try:
            # Buscamos un token que coincida, sea de la agencia, 
            # NO este vencido (vencimiento > ahora)
            # y NO este validado aun (para evitar reuso)
            token_record = request.env['x_tokens_sinergia_bda'].sudo().search([
                ('x_name', '=', token),
                ('x_studio_nombre_agencia', '=', agencia),
                ('x_studio_vencimiento', '>', datetime.now()), 
                ('x_studio_validado', '=', False)
            ], limit=1)

            if token_record:
                # SI ES VALIDO: Lo marcamos como usado (True)
                token_record.write({'x_studio_validado': True})
                return {'success': True}
            else:
                # NO ENCONTRADO O VENCIDO
                return {'success': False, 'error': 'El código es incorrecto, ha vencido o ya fue utilizado.'}

        except Exception as e:
            _logger.error(f"Error validando token: {str(e)}")
            return {'success': False, 'error': str(e)}