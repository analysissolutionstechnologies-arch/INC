#


# -*- coding: utf-8 -*-
from odoo import api, fields, models

import json
# from cryptography.fernet import Fernet
import requests
from datetime import datetime
import base64

from Crypto.Cipher import DES3
from Crypto.Hash import MD5
from Crypto.Util.Padding import pad, unpad
from base64 import b64encode, b64decode
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError


def encrypt_netfinance(mensaje, hash_key):
    # Convertir el hash_key a bytes
    key_bytes = hash_key.encode('utf-8')
    
    # Crear el hash MD5 de la clave
    md5 = MD5.new()
    md5.update(key_bytes)
    key = md5.digest()
    
    # Crear el objeto TripleDES con la clave y modo ECB
    cipher = DES3.new(key, DES3.MODE_ECB)
    
    # Convertir el mensaje a bytes y aplicar padding
    mensaje_bytes = mensaje.encode('utf-8')
    padded_mensaje = pad(mensaje_bytes, DES3.block_size)
    
    # Encriptar el mensaje
    encrypted_bytes = cipher.encrypt(padded_mensaje)
    
    # Convertir el resultado encriptado a una cadena base64
    encrypted_message = base64.b64encode(encrypted_bytes).decode('utf-8')
    
    return encrypted_message


class ResPartner(models.Model):

    _inherit = "res.partner"
   
    partner_idPersona = fields.Char(string="Id Persona")
    municipio_id = fields.Many2one( 'res.municipiogt',string="Municipio")
    zona_id = fields.Many2one( 'res.zonagt',string="Zona")
    colonia_id = fields.Many2one( 'res.coloniagt',string="Colonia")
    departamento_id = fields.Many2one( 'res.country.state',string="Departamento")
    documento_personal_identificacion = fields.Char('DPI')
    respuesta_cliente_netfinance = fields.Text('Respuesta Netfinance')
    ID_CIUDAD = fields.Char(
        string="ID CIUDAD",
    )
    ID_ZONA = fields.Char(
        string="ID ZONA",
    )
    ID_COLONIA = fields.Char(
        string="ID COLONIA",
    )




    def get_autorization_netfinance_cipher(self):
        record = self
        # Datos proporcionados
        token = record.env.company.token_netfinance
        print("Verificar FORMATO", datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
        json_data = {
            "Cliente": record.env.company.cliente_netfinance,
            "Credencial": record.env.company.credencial_netfinance,
            "Token": record.env.company.token_netfinance,
            "FechaSolicitudApi": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        }
        print("VERIFICAR DATA", json_data)

        hash_key = record.env.company.hash_key_netfinance
        json_string = json.dumps(json_data)


        # Encriptar el mensaje
        encriptado = encrypt_netfinance(json_string, hash_key)
        print(encriptado)

        # Encriptar los datos
        return encriptado
    
    def search_zonagt(self , id_data):
        search_zonagt = self.env['res.zonagt'].search([('ID_SECTOR', '=', id_data)])
        if not search_zonagt:
            search_zonagt = self.env['res.zonagt'].search([('code', '=', id_data)])
        if not search_zonagt:
            id_data = int(id_data)
            search_zonagt = self.env['res.zonagt'].search([('code', '=', id_data)])

        return  search_zonagt
    

    def search_municipiogt(self , id_data):
        search_zonagt = self.env['res.municipiogt'].search([('ID_CIUDAD', '=', id_data)])
        if not search_zonagt:
            id_data = int(id_data)
            search_zonagt = self.env['res.municipiogt'].search([('ID_CIUDAD', '=', id_data)])

        return  search_zonagt
    
    def search_coloniagt(self ,id_data):

        search_zonagt = self.env['res.coloniagt'].search([('ID_BARRIO', '=', id_data)])

        if not search_zonagt:
            search_zonagt = self.env['res.coloniagt'].search([('ID_BARRIO', '=', id_data)])
        if not search_zonagt:
            id_data = int(id_data)
            search_zonagt = self.env['res.coloniagt'].search([('ID_BARRIO', '=', id_data)])
        return  search_zonagt


    def get_autorization_cliente_netfinance(self):
        #"EndPoint Información de Autorización Crédito"
        for record in self:
            print("get_autorization_cliente_netfinance")
             
            print("get_autorization_cliente_netfinance")
            encrypted_data = record.get_autorization_netfinance_cipher()
            url = record.env.company.url_netfinance_conect  + "AutorizacionesCredito/Cliente" 
            char_cliente_dpi = record.documento_personal_identificacion
            if not char_cliente_dpi:
                raise UserError("Debes agregar una Autorizacion Netfinance")
            
            url = url + "?parametro=" + str(char_cliente_dpi)

            print("VERIFICAR URL DPI_CLIENTE" , url)
             
            authorization_header = {
                    "Authorization": encrypted_data
                    }
            print("VERIFICAR authorization_header" , authorization_header)
            response = requests.get(url, headers=authorization_header, verify=False)
            # response = requests.get(url, headers=authorization_header)
            record.respuesta_cliente_netfinance = response.text
            print("VERIFICAR RESPONSE" , response)
            if response.status_code == 200:
                datos_response = response.json()
                print("VERIFICAR DATOS RESPONSE" , datos_response)
                partner_name = datos_response["data"]["Cliente"]["NombreCompleto"]
                nit_netfinance = datos_response["data"]["Cliente"]["Nit"]
                dpi_netfinance = char_cliente_dpi
                
                partner_phone = datos_response["data"]["Cliente"]["NumeroTelefono"]
                partner_idPersona = datos_response["data"]["Cliente"]["IdPersona"]
                partner_Departamento = datos_response["data"]["Direccion"]["Departamento"]
                partner_Municipio = datos_response["data"]["Direccion"]["Municipio"]
                partner_Zona = datos_response["data"]["Direccion"]["Zona"]
                partner_Colonia = datos_response["data"]["Direccion"]["Colonia"]
                partner_street = datos_response["data"]["Direccion"]["NumeroCasa"]
                partner_street2 = datos_response["data"]["Direccion"]["Calle"]
                street = partner_street + " " + partner_street2
                partner_Referencia = datos_response["data"]["Direccion"]["Referencia"]
                stree2 = partner_Referencia

                print("VERIFICAR partner_Zona" , partner_Zona)
                print("VERIFICAR partner_Municipio" , partner_Municipio)
                print("VERIFICAR partner_Colonia" , partner_Colonia)

                # len_municipio = len(partner_Municipio)
                # len_zona = len(partner_Zona)
                # partner_Zona = partner_Zona[len_municipio:]
                # partner_Colonia = partner_Colonia[len_zona:]
                # ID_CIUDAD = partner_Municipio
                # ID_ZONA = partner_Zona
                # ID_COLONIA = partner_Colonia



                # print("VERIFICAR partner_Zona" , partner_Zona)
                # print("VERIFICAR partner_Colonia" , partner_Colonia)
                # zona_id = self.search_zonagt(id_data=partner_Zona)
                # municipio_id = self.search_municipiogt(id_data=partner_Municipio)
                # colonia_id = self.search_coloniagt(id_data=partner_Colonia)
                
                
                # if not zona_id:
                #     zona_id = self.search_zonagt( int(partner_Zona) )
                # if not municipio_id:
                #     municipio_id = self.search_municipiogt( int(partner_Municipio) )
                # if not colonia_id:
                #     colonia_id = self.search_coloniagt( int(partner_Colonia) )

                # print("VERIFICAR zona_id" , zona_id)
                # print("VERIFICAR municipio_id" , municipio_id )
                # print("VERIFICAR colonia_id" , colonia_id )
                
                
                record.write({
                        'name': partner_name,
                        'vat': nit_netfinance,
                        'documento_personal_identificacion': dpi_netfinance,
                        'partner_idPersona': partner_idPersona,
                        'phone': partner_phone,
                        'street': street,
                        'street2': stree2,
                        # 'departamento_id': municipio_id.state_id.id,
                        # 'municipio_id': municipio_id.id,
                        # 'zona_id': zona_id.id,
                        # 'colonia_id': colonia_id.id,
                        # 'ID_CIUDAD': ID_CIUDAD,
                        # 'ID_ZONA': ID_ZONA,
                        # 'ID_COLONIA': ID_COLONIA,
                        })
                 