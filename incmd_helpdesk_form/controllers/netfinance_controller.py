# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json
import base64
import requests
from datetime import datetime

from Crypto.Cipher import DES3
from Crypto.Hash import MD5
from Crypto.Util.Padding import pad


def encrypt_netfinance(mensaje, hash_key):
    key_bytes = hash_key.encode('utf-8')
    md5 = MD5.new()
    md5.update(key_bytes)
    key = md5.digest()[:24]

    cipher = DES3.new(key, DES3.MODE_ECB)
    mensaje_bytes = mensaje.encode('utf-8')
    padded_mensaje = pad(mensaje_bytes, DES3.block_size)
    encrypted_bytes = cipher.encrypt(padded_mensaje)
    return base64.b64encode(encrypted_bytes).decode('utf-8')


class NetfinanceWebsiteController(http.Controller):

    def _get_authorization_cipher(self):
        company = request.env.company.sudo()

        json_data = {
            "Cliente": company.cliente_netfinance,
            "Credencial": company.credencial_netfinance,
            "Token": company.token_netfinance,
            "FechaSolicitudApi": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        }

        json_string = json.dumps(json_data)
        return encrypt_netfinance(json_string, company.hash_key_netfinance)

    @http.route('/consultar/autorizacion', type='json', auth='public', website=True, csrf=False)
    def consultar_autorizacion(self, **kwargs):
        try:
            payload = request.httprequest.get_json(silent=True) or {}
            autorizacion = payload.get('autorizacion')

            if not autorizacion:
                return {
                    'ok': False,
                    'message': 'Debe ingresar el número de autorización.'
                }

            autorizacion = ''.join(ch for ch in str(autorizacion) if ch.isdigit())

            if not autorizacion:
                return {
                    'ok': False,
                    'message': 'La autorización solo debe contener números.'
                }

            company = request.env.company.sudo()
            encrypted_data = self._get_authorization_cipher()

            url = company.url_netfinance_conect + "AutorizacionesCredito/Autorizacion"
            url = url + "?parametro=" + str(autorizacion)

            headers = {
                "Authorization": encrypted_data
            }

            response = requests.get(url, headers=headers, verify=False, timeout=30)

            if response.status_code != 200:
                return {
                    'ok': False,
                    'message': 'Error en la respuesta del servidor Netfinance.'
                }

            datos_response = response.json() or {}

            if not datos_response.get("data"):
                return {
                    'ok': False,
                    'message': 'La respuesta no contiene datos.'
                }

            if not datos_response["data"].get("Autorizacion"):
                return {
                    'ok': False,
                    'message': 'Validar el código de autorización.'
                }

            cliente = datos_response["data"].get("InformacionCliente", {}).get("Cliente", {})
            direccion = datos_response["data"].get("InformacionCliente", {}).get("Direccion", {})
            autorizacion_data = datos_response["data"].get("Autorizacion", {})

            numero_casa = (direccion.get("NumeroCasa") or "").strip()
            calle = (direccion.get("Calle") or "").strip()
            referencia = (direccion.get("Referencia") or "").strip()

            direccion_final = " ".join([x for x in [numero_casa, calle] if x]).strip()
            if referencia:
                direccion_final = (direccion_final + " " + referencia).strip()

            nit = (cliente.get("Nit") or "").replace(" ", "").replace("-", "").replace(".", "")
            nombre = (cliente.get("NombreCompleto") or "").strip()
            telefono = (cliente.get("NumeroTelefono") or "").strip()
            dpi = (autorizacion_data.get("DpiCliente") or "").strip()
            factura = autorizacion_data.get("Factura", "") or ""
            pagare = autorizacion_data.get("Pagare", "") or ""
            poe = autorizacion_data.get("POE", "") or ""

            if not nombre or not telefono or not nit or not dpi or not direccion_final:
                return {
                    'ok': False,
                    'message': 'La autorización no devolvió todos los datos requeridos del cliente.'
                }

            return {
                'ok': True,
                'message': 'Autorización consultada correctamente.',
                'data': {
                    'nombre': nombre,
                    'telefono': telefono,
                    'nit': nit,
                    'dpi': dpi,
                    'direccion': direccion_final,
                    'factura': factura,
                    'pagare': pagare,
                    'poe': poe
                }
            }

        except Exception as e:
            return {
                'ok': False,
                'message': str(e)
            }