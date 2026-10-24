# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

import json
import requests
from datetime import datetime
import base64

from Crypto.Cipher import DES3
from Crypto.Hash import MD5
from Crypto.Util.Padding import pad, unpad
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
import _strptime  # Esto define PY_SSIZE_T_CLEAN

def encrypt_netfinance(mensaje, hash_key):
    try:
 
        # Convertir el hash_key a bytes
        key_bytes = hash_key.encode('utf-8')
        
        # Crear el hash MD5 de la clave
        md5 = MD5.new()
        md5.update(key_bytes)
        key = md5.digest()

        # Ajustar el tamaño de la clave a 24 bytes
        key = key[:24]

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
    except Exception as e:
        raise UserError(f"Error en la encriptación de datos: {str(e)}")

class SaleOrder(models.Model):
    _inherit = "sale.order"

    respuesta_cliente_netfinance = fields.Text(string="Respuesta Netfinance" , copy=False)
    respuesta_autorizacion_netfinance = fields.Text(string="Respuesta Autorizacion Netfinance", copy=False)
    respuesta_cuota_netfinance = fields.Text(string="Respuesta Cuota Netfinance", copy=False)
    check_autorization_netfinance = fields.Boolean(string="Autorizacion Netfinance", copy=False)
    char_autorization_netfinance = fields.Char(string="Nro Autorizacion Netfinance", copy=False)
    char_cliente_dpi = fields.Char(string="Nro Cliente Autorizacion", copy=False , related='partner_id.documento_personal_identificacion', store=True)


    validar_dpi = fields.Boolean(string="Validar DPI" , compute="compute_validar_datos_netfinance", copy=False)
    validar_autorizaion = fields.Boolean(string="Validar Autorización" , compute="compute_validar_datos_netfinance", copy=False)
    validar_Idpersona = fields.Boolean(string="Validar IdPersona" , compute="compute_validar_datos_netfinance", copy=False)
    validar_articulos = fields.Boolean(string="Validar Generico" , copy=False)
    validar_monto = fields.Boolean(string="Validar Monto" , compute="compute_validar_datos_netfinance", copy=False)
    validar_agencia = fields.Boolean(string="Validar Agencia" , compute="compute_validar_datos_netfinance", copy=False)
    validar_monto_plus = fields.Boolean(string="Validar Japon Plus" , compute="compute_validar_datos_netfinance", copy=False)

    # Verificar Autorizacion 
    DpiCliente_autorizado = fields.Char(string="DpiCliente Netfinance", copy=False)
    Factura_monto_autorizado = fields.Char(string="Total Factura Netfinance", copy=False) 
    Pagare_monto_autorizado = fields.Char(string="Pagare Netfinance", copy=False) 
    Agencia_autorizada = fields.Char(string="Agencia Netfinance", copy=False) 
    IdPersona_autorizada = fields.Char(string="IdPersona Netfinance", copy=False) 
    cuota_autorizada = fields.Char(string="Cuota Netfinance", copy=False)
    porcentaje_descuento_autorizado = fields.Char(string="PorcentajeDescuento Netfinance", copy=False)
    tipo_cliente_autorizado = fields.Char(string="TipoCliente Netfinance", copy=False)
    monto_plus_autorizado = fields.Char(string="Japon Plus Netfinance", copy=False)
    monto_plus_manual = fields.Char(string="Japon Plus Odoo", copy=False)
    enganche_autorizado = fields.Char(string="Enganche Netfinance", copy=False)
    articulo_autorizado = fields.Char(string="Generico NetfinanceE", copy=False)
    TipoFlujo = fields.Char(string="TipoFlujo Netfinance", copy=False)
    Plazo = fields.Char(string="Plazo Netfinance", copy=False)
    poe_autorizado = fields.Float(string='POE Autorizado Netfinance', store=True)
    check_monto_factura = fields.Boolean(string="Checar Monto Factura", compute="compute_check_monto_factura", copy=False)
    check_monto_poe = fields.Boolean(string="Checar Monto POE", compute="compute_check_monto_poe", copy=False)
    diff_montos = fields.Float(string="Diferencia Montos", copy=False)
    # SE AGREGO EL NUEVO CAMPO SI ES BDA LA AGENCIA
    Agencia_BDA = fields.Boolean(string="Es Agencia BDA", copy=False)

    lista_articulos = fields.Json(string="Genericos Odoo", copy=False , compute="compute_articulos_en_lineas")

    @api.depends('Factura_monto_autorizado', 'amount_total')
    def compute_check_monto_factura(self):
        for record in self:
            record.check_monto_factura = True
            if record.Factura_monto_autorizado:
                total_factura = record.amount_total
                Factura_monto_autorizado = float(record.Factura_monto_autorizado.replace(',', '') )
                # Factura_monto_autorizado = record.Factura_monto_autorizado.replace(',', '').isdigit()
                diff_montos_totales = abs( round( total_factura - Factura_monto_autorizado, 2) )
                record.diff_montos = round(diff_montos_totales, 2)
                if diff_montos_totales > 0.03:
                    record.check_monto_factura = False
                    
                    
    @api.depends('poe_autorizado', 'order_line')
    def compute_check_monto_poe(self):
        for record in self:
            record.check_monto_poe = True
            
            if record.pricelist_id and record.pricelist_id.name == "CRÉDITO":
               total_poe = sum(line.price_list * line.product_uom_qty for line in record.order_line)
               if abs(total_poe - record.poe_autorizado) > 0.01:
                   record.check_monto_poe = False

    def _prepare_invoice(self):
        self.ensure_one()

        values = super(SaleOrder, self)._prepare_invoice()
        # if self.char_autorization_netfinance:
        #     values['char_autorization_netfinance'] = self.char_autorization_netfinance

        # if self.DpiCliente_autorizado:
        #     values['DpiCliente_autorizado'] = self.DpiCliente_autorizado
        #     values['Factura_monto_autorizado'] = self.Factura_monto_autorizado
        #     values['Pagare_monto_autorizado'] = self.Pagare_monto_autorizado
        #     values['Agencia_autorizada'] = self.Agencia_autorizada
        #     values['IdPersona_autorizada'] = self.IdPersona_autorizada
        # if self.cuota_autorizada:
        #     values['cuota_autorizada'] = self.cuota_autorizada
        # if self.porcentaje_descuento_autorizado:
        #     values['porcentaje_descuento_autorizado'] = self.porcentaje_descuento_autorizado
        # if self.tipo_cliente_autorizado:
        #     values['tipo_cliente_autorizado'] = self.tipo_cliente_autorizado
        # if self.monto_plus_autorizado:
        #     values['monto_plus_autorizado'] = self.monto_plus_autorizado
        # if self.enganche_autorizado:
        #     values['enganche_autorizado'] = self.enganche_autorizado
        # if self.TipoFlujo:
        #     values['TipoFlujo'] = self.TipoFlujo
        # if self.Plazo:
        #     values['Plazo'] = self.Plazo
            
        values['sale_order_incomel_id'] = self.id
        print("VALUES PREPARE INVOICE", values)
            
        return values
    
    def compute_articulos_en_lineas(self):
        for record in self:
            print("COMPUTE ARTICULOS EN LINEAS")
            lista_articulos = []
            for line in record.order_line:
                categoria = line.product_id.categ_id.name
                lista_articulos.append( categoria)
            print("LISTA ARTICULOS", lista_articulos)

            record.lista_articulos = lista_articulos
            print("LISTA ARTICULOS", record.lista_articulos)



    @api.depends('partner_id', 'monto_plus_autorizado',
                 'monto_plus_manual','amount_total', 'journal_id',
                 'IdPersona_autorizada', 'Agencia_autorizada', 'Pagare_monto_autorizado',
                 'check_autorization_netfinance')
    def compute_validar_datos_netfinance(self):
        for record in self:
            record.validar_dpi = False
            record.validar_articulos = False
            record.validar_monto = False
            record.validar_agencia = False
            record.validar_autorizaion = False
            record.validar_Idpersona = False
#            record.validar_monto_plus = False

            if record.order_line and record.lista_articulos and record.articulo_autorizado in record.lista_articulos:#verificar
                    
                    record.validar_articulos = True

            if record.partner_id:
                if record.DpiCliente_autorizado and record.DpiCliente_autorizado == record.partner_id.documento_personal_identificacion:
                    record.validar_dpi = True
            
            # if record.amount_total:
            #     if record.Factura_monto_autorizado and float(record.Factura_monto_autorizado) >= record.amount_total:
            #         record.validar_monto = True
            
            if record.Agencia_autorizada:
                if record.Agencia_autorizada == record.journal_id.name:
                    record.validar_agencia = True
            
            if record.check_autorization_netfinance:
                record.validar_agencia = True
            
            # se comenta funcionalidad para validar JAPON PLUS
            #if record.monto_plus_autorizado:
            #    if record.monto_plus_autorizado == record.monto_plus_manual:
            #        record.validar_monto_plus = True
            
            if(record.validar_dpi and record.validar_articulos and record.validar_agencia
                and record.check_monto_poe and record.check_monto_factura):
                record.validar_autorizaion = True

    def get_autorization_netfinance_cipher(self):
        try:
            record = self
            json_data = {
                "Cliente": record.env.company.cliente_netfinance,
                "Credencial": record.env.company.credencial_netfinance,
                "Token": record.env.company.token_netfinance,
                "FechaSolicitudApi": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            }
            hash_key = record.env.company.hash_key_netfinance
            json_string = json.dumps(json_data)

            # Encriptar el mensaje
            encriptado = encrypt_netfinance(json_string, hash_key)
            print("VERIFICAR CIPHER: ", encriptado)

            return encriptado
        except Exception as e:
            raise UserError(f"Error al obtener la autorización cifrada: {str(e)}")

    def get_autorization_netfinance(self):
        for record in self:
            encrypted_data = record.get_autorization_netfinance_cipher()
            url = record.env.company.url_netfinance_conect + "AutorizacionesCredito/Autorizacion"    
            char_autorization_netfinance = record.char_autorization_netfinance
            if not char_autorization_netfinance:
                raise UserError("Debes agregar una Autorizacion Netfinance")
            url = url + "?parametro=" + str(char_autorization_netfinance)

            print("VERIFICAR URL", url)
            authorization_header = {
                "Authorization": encrypted_data
            }
            print("VERIFICAR authorization_header", authorization_header)
            response = requests.get(url, headers=authorization_header, verify=False)
            record.respuesta_autorizacion_netfinance = response.text
            print("VERIFICAR RESPONSE", response)
            if response.status_code == 200:
                datos_response = response.json()
                print("VERIFICAR DATOS RESPONSE", datos_response)
                if datos_response.get("data") is None:
                    raise UserError(f"Error en la respuesta del servidor Netfinance: {response.text}")
                if datos_response.get("data") and datos_response["data"].get("Autorizacion") is None:
                    raise UserError(f"Validar el código de autorización")
                
                else:
                    # Asignar datos de autorización
                    record.DpiCliente_autorizado = datos_response["data"]["Autorizacion"]["DpiCliente"]
                    record.Factura_monto_autorizado = datos_response["data"]["Autorizacion"]["Factura"]
                    record.Pagare_monto_autorizado = datos_response["data"]["Autorizacion"]["Pagare"]
                    record.cuota_autorizada = datos_response["data"]["Autorizacion"]["Cuota"]
                    record.Agencia_autorizada = datos_response["data"]["Autorizacion"]["Agencia"]
                    record.IdPersona_autorizada = datos_response["data"]["InformacionCliente"]["Cliente"]["IdPersona"]
                    record.porcentaje_descuento_autorizado = datos_response["data"]["Autorizacion"]["PorcentajeDescuento"]
                    record.tipo_cliente_autorizado = datos_response["data"]["Autorizacion"]["TipoCliente"]
                    record.monto_plus_autorizado = datos_response["data"]["Autorizacion"]["MontoPlus"]
                    record.enganche_autorizado = datos_response["data"]["Autorizacion"]["Enganche"]
                    # SE ASIGNA EL NUEVO CAMPO SI ES BDA LA AGENCIA
                    record.Agencia_BDA = datos_response["data"]["Autorizacion"]["Agencia_BDA"]
                    

                    if datos_response["data"]["Autorizacion"].get("POE"):
                        record.poe_autorizado = datos_response["data"]["Autorizacion"]["POE"]

                    if datos_response["data"]["Autorizacion"].get("Artículo"):
                        record.articulo_autorizado = datos_response["data"]["Autorizacion"]["Artículo"]
                        
                    if datos_response["data"]["Autorizacion"].get("TipoFlujo"):
                        record.TipoFlujo = datos_response["data"]["Autorizacion"]["TipoFlujo"]
                        
                    if datos_response["data"]["Autorizacion"].get("Plazo"):
                        record.Plazo = datos_response["data"]["Autorizacion"]["Plazo"]

                    # Buscar o crear cliente usando función común
                    record._buscar_o_crear_cliente(datos_response["data"])
                    

            else:
                raise UserError(f"Error en la respuesta del servidor Netfinance: {response.text}")

    def get_autorization_cliente_netfinance(self):
        for record in self:
            encrypted_data = record.get_autorization_netfinance_cipher()
            url = record.env.company.url_netfinance_conect + "AutorizacionesCredito/Cliente"
            char_cliente_dpi = record.char_cliente_dpi
            if not char_cliente_dpi:
                raise UserError("Debes agregar una Autorizacion Netfinance")
            
            url = url + "?parametro=" + str(char_cliente_dpi)

            print("VERIFICAR URL DPI_CLIENTE", url)
            authorization_header = {
                "Authorization": encrypted_data
            }
            print("VERIFICAR authorization_header", authorization_header)
            response = requests.get(url, headers=authorization_header, verify=False)
            record.respuesta_cliente_netfinance = response.text
            print("VERIFICAR RESPONSE", response)
            if response.status_code == 200:
                datos_response = response.json()
                print("VERIFICAR DATOS RESPONSE", datos_response)
                # Buscar o crear cliente usando función común
                record._buscar_o_crear_cliente(datos_response["data"])
            else:
                raise UserError(f"Error en la respuesta del servidor Netfinance: {response.text}")

    def _buscar_o_crear_cliente(self, datos):
        self.ensure_one()
        
        # Obtener datos del cliente
        nombre_cliente = datos["InformacionCliente"]["Cliente"]["NombreCompleto"]
        nit_cliente = datos["InformacionCliente"]["Cliente"]["Nit"].replace(" ", "").replace("-", "").replace(".", "")
        dpi_cliente =  datos["Autorizacion"]["DpiCliente"]
        
        # Buscar cliente por diferentes criterios
        partner = self.env['res.partner'].search([
            ('documento_personal_identificacion', '=', dpi_cliente),
            ('vat', '=', nit_cliente)
        ], limit=1)

        if not partner:
            partner = self.env['res.partner'].search([
                '|',
                ('documento_personal_identificacion', '=', dpi_cliente),
                ('vat', '=', nit_cliente)
            ], limit=1)

        if len(partner) > 1:
            raise UserError("El cliente se encuentra duplicado o tiene más de un nombre, DPI o NIT en la base de datos.")

        asignar_tarifa_cliente = self.env['product.pricelist'].search([('name', '=', 'CRÉDITO')], limit=1)
        if not asignar_tarifa_cliente:
            asignar_tarifa_cliente = self.env['product.pricelist'].search([('name', 'ilike', 'CRÉDITO')], limit=1)
            
        if not asignar_tarifa_cliente:
            asignar_tarifa_cliente = self.env['product.pricelist'].search([('name', 'ilike', 'CREDITO')], limit=1)
            
        if not asignar_tarifa_cliente:
            asignar_tarifa_cliente = self.env['product.pricelist'].search([('name', 'ilike', 'DITO')], limit=1)

        # Preparar datos comunes
        vals = {
            'name': nombre_cliente,
            'vat': nit_cliente,
            'documento_personal_identificacion': dpi_cliente,
            'phone': datos["InformacionCliente"]["Cliente"]["NumeroTelefono"],
            'partner_idPersona': datos["InformacionCliente"]["Cliente"]["IdPersona"],
            'street': datos["InformacionCliente"]["Direccion"]["NumeroCasa"] + " " + datos["InformacionCliente"]["Direccion"]["Calle"],
            'street2': datos["InformacionCliente"]["Direccion"]["Referencia"],
            'property_product_pricelist': asignar_tarifa_cliente.id
        }

        if partner:
            partner.write(vals)
            print("Cliente Netfinance ACTUALIZADO")
        else:
            partner = self.env['res.partner'].create(vals)
            print("Cliente Netfinance CREADO")

        self.partner_id = partner.id
        return partner

    def get_autorization_cuotas_netfinance(self):
        for record in self:
            encrypted_data = record.get_autorization_netfinance_cipher()
            url_company = record.env.company.url_netfinance_conect   
            url_sin_api = url_company.replace("api", "Paginas")
            url = url_sin_api + "Autorizacion/CotizadorCredito.aspx/Cuota"

            char_autorization_netfinance = record.char_autorization_netfinance
            if not char_autorization_netfinance:
                raise UserError("Debes agregar una Autorizacion Netfinance")
            
            url = url + "?parametro=" + str(char_autorization_netfinance)

            print("VERIFICAR URL DPI_CLIENTE", url)
            authorization_header = {
                "Authorization": encrypted_data
            }
            
            print("VERIFICAR authorization_header", authorization_header)
            response = requests.post(url, headers=authorization_header, verify=False)
            record.respuesta_cuota_netfinance = response.text
            print("VERIFICAR RESPONSE", response)
            if response.status_code != 200:
                raise UserError(f"Error en la respuesta del servidor Netfinance: {response.text}")

    def action_confirm(self):
        for record in self:
            if record.char_autorization_netfinance:
                if not record.validar_dpi:
                    raise ValidationError(f"El DPI del cliente en Odoo no coincide con el DPI de la Autorización de NetFinance.")
                # if not record.validar_monto:
                #     raise ValidationError(f"El monto de la factura es mayor o menor que {record.monto_autorizado}, el total factura de la autorización de crédito.")
                if not record.validar_articulos:
                    raise ValidationError(f"El Articulo con mayor valor no esta dentro del pedido de venta {record.articulo_autorizado}.")
                # if not record.validar_Idpersona:
                #     raise ValidationError(f"El IdPersona para autorizar no coincide con el del cliente.")
                
                if not record.check_monto_factura:
                    Factura_monto_autorizado = float(record.Factura_monto_autorizado.replace(',', '') )
                    diff_factura = round(record.amount_total - Factura_monto_autorizado , 4)
                    raise ValidationError(f"El monto de la factura %s no coincide con el monto autorizado!!! %s. \n Por favor verifique los datos diff %s" % (record.amount_total, Factura_monto_autorizado , diff_factura))
                
                if not record.check_monto_poe:
                    raise ValidationError(f"El monto del POE %s no coincide con el POE autorizado %s." % (record.poe_autorizado, record.poe_autorizado))
                
                if record.char_autorization_netfinance and not record.validar_autorizaion:
                        raise ValidationError(f"Disculpe, al parecer no tiene una autorización para este crédito.")
                    
            return super(SaleOrder, self).action_confirm()

    
