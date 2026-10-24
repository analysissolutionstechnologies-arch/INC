# -*- coding: utf-8 -*-

import time
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
import requests
import logging
import base64
from lxml import etree
from lxml.builder import ElementMaker
import xml.etree.ElementTree as ET
import datetime

class AccountMove(models.Model):
    _inherit = "account.move"

    fel_numero_abonos_fc = fields.Integer('No. abonos FCAM')
    fel_fecha_vencimiento_fc = fields.Date('Fecha vencimiento FCAM')
    fel_monto_abonos_fc = fields.Float('Monto abonos FCAM')
    fel_numero_autorizacion = fields.Char('Número de autorización', copy=False, tracking=True)
    fel_serie = fields.Char('Serie', copy=False, tracking=True)
    fel_numero = fields.Char('Número', copy=False, tracking=True)
    # fel_uuid = fields.Char('UUID')
    fel_documento_certificado = fields.Char('Documento FEL', copy=False, tracking=True)
    fel_incoterm = fields.Selection([
            ('EXW', 'En fábrica'),
            ('FCA', 'Libre transportista'),
            ('FAS', 'Libre al costado del buque'),
            ('FOB', 'Libre a bordo'),
            ('CFR', 'Costo y flete'),
            ('CIF','Costo, seguro y flete'),
            ('CPT','Flete pagado hasta'),
            ('CIP','Flete y seguro pagado hasta'),
            ('DDP','Entregado en destino con derechos pagados'),
            ('DAP','Entregada en lugar'),
            ('DAT','Entregada en terminal'),
            ('ZZZ','Otros')
        ],string="Incoterm",default="EXW",
        help="Termino de entrega")
    tipo_factura = fields.Selection([('venta','Venta'),('compra', 'Compra o Bien'), ('servicio', 'Servicio'),('varios','Varios'), ('combustible', 'Combustible'),('importacion', 'Importación'),('exportacion','Exportación')],
        string="Tipo de factura")
    fel_no_enviar_tel = fields.Boolean('No enviar telefono fel')

# 4 1 , exportacion
    def fecha_hora_factura(self, fecha):
        fecha_convertida = datetime.datetime.strptime(str(fecha), '%Y-%m-%d').date().strftime('%Y-%m-%d')
        hora = datetime.datetime.strftime(fields.Datetime.context_timestamp(self, datetime.datetime.now()), "%H:%M:%S")
        fecha_hora_emision = str(fecha_convertida)+'T'+str(hora)
        return fecha_hora_emision


    def verificar_lineas_sin_impuestos(self, lineas):
        linea_sin_impuesto = False
        for linea in lineas:
            if len(linea.tax_ids) == 0:
                linea_sin_impuesto = True

        return linea_sin_impuesto

    def _post(self,soft=True):
        for factura in self:
            if factura.move_type not in ['out_invoice', 'out_refund', 'in_invoice'] and not factura.pos_order_ids:
                return super(AccountMove, self)._post(soft)

                #  Aquí permitimos la certificación FEL solo en facturas (`out_invoice`)
            if factura.move_type in ['out_invoice', 'out_refund', 'in_invoice']:
                if not factura.journal_id.fel_tipo_dte:  # Si el diario no tiene FEL activado, no certificamos
                    return super(AccountMove, self)._post(soft)

                logging.warn(f"Procesando certificación FEL para la factura: {factura.name}")

            if factura.fel_serie and factura.fel_numero_autorizacion and factura.journal_id.fel_tipo_dte:
                raise UserError(str('NO PUEDE VALIDAR FACTURA DE NUEVO POR QUE YA FUE CERTIFICADA UNA VEZ'))

            if factura.journal_id and factura.journal_id.fel_tipo_dte:
                logging.warn(factura)
                # Definimos SHEMALOCATION
                lista_impuestos = []

                attr_qname = etree.QName("http://www.w3.org/2001/XMLSchema-instance", "schemaLocation")
                DTE_NS = "{http://www.sat.gob.gt/dte/fel/0.2.0}"
                # Nuevo SMAP
                NSMAP = {
                    "ds": "http://www.w3.org/2000/09/xmldsig#",
                    "dte": "http://www.sat.gob.gt/dte/fel/0.2.0",
                    "xsi": "http://www.w3.org/2001/XMLSchema-instance"
                }

                fecha_factura = factura.invoice_date if factura.invoice_date else fields.Date.context_today(self)

                try:
                    fecha = datetime.datetime.strptime(str(fecha_factura), '%Y-%m-%d').date().strftime('%Y-%m-%d')
                except ValueError:
                    raise UserError('La fecha de la factura no es válida. Verifique el campo invoice_date.')

                hora = datetime.datetime.strftime(fields.Datetime.context_timestamp(self, datetime.datetime.now()),
                                                  "%H:%M:%S")
                fecha_hora_emision = str(fecha) + 'T' + str(hora)

                moneda = str(factura.currency_id.name)
                tipo = factura.journal_id.fel_tipo_dte

# Se comento para permitir hacer facturas con fecha anterior
#                if factura.invoice_date != True:
#                    factura.invoice_date = fields.Date.context_today(self)

              #  moneda = str(factura.currency_id.name)
              #  fecha = datetime.datetime.strptime(str(factura.invoice_date), '%Y-%m-%d').date().strftime('%Y-%m-%d')
              #  hora = datetime.datetime.strftime(fields.Datetime.context_timestamp(self, datetime.datetime.now()), "%H:%M:%S")
              #  fecha_hora_emision = self.fecha_hora_factura(factura.invoice_date)
              #  tipo = factura.journal_id.fel_tipo_dte
                # if tipo == 'FACT':
                #
                # if tipo == 'NDEB':
                #
                motivo_nc = ''
                factura_original_id = False
                if tipo == 'NCRE':
                    # Validamos si la factura original existe antes de operar sobre `ref`
                    if factura.ref and ':' in factura.ref:
                        ref_parts = factura.ref.split(':')
                        if len(ref_parts) > 1:
                            factura_original_id = self.env['account.move'].search([
                                ('name', '=', ref_parts[1].split()[0].replace(",", ""))
                            ])
                    else:
                        raise UserError('La referencia a la factura original no es válida.')

                    if factura_original_id and factura.currency_id.id == factura_original_id.currency_id.id:
                        ref_text = factura.ref.split(':')[1].split()
                        if ref_text:
                            ref_text.pop(0)
                            motivo_nc = " ".join(ref_text) if ref_text else 'Nota de crédito'
                        logging.warn('Si es nota crédito')
                    else:
                        raise UserError('NOTA DE CRÉDITO DEBE DE SER CON LA MISMA MONEDA QUE LA FACTURA ORIGINAL')



                datos_generales = {
                    "CodigoMoneda": moneda,
                    "FechaHoraEmision":fecha_hora_emision,
                    "NumeroAcceso": str(100000000),
                    "Tipo":tipo
                    }
                if tipo == 'FACT' and factura.tipo_factura == "exportacion":
                    datos_generales['Exp'] = "SI"



                nit_company = "CF"
                if '-' in factura.company_id.vat:
                    nit_company = factura.company_id.vat.replace('-','')
                else:
                    nit_company = factura.company_id.vat

                datos_emisor = {
                    "AfiliacionIVA":"GEN",
                    "CodigoEstablecimiento": str(factura.journal_id.fel_codigo_establecimiento) or "",
                    "CorreoEmisor": str(factura.company_id.email) or "",
                    "NITEmisor": str(nit_company),
                    # "NITEmisor": '103480307',
                    "NombreComercial": factura.journal_id.fel_nombre_comercial or "",
                    "NombreEmisor": factura.company_id.company_registry or ""
                }

                nit_partner = "CF"
                if factura.partner_id.vat:
                    if '-' in factura.partner_id.vat:
                        nit_partner = factura.partner_id.vat.replace('-','')
                    else:
                        nit_partner = factura.partner_id.vat

                if factura.amount_total > 2500:
                    if (nit_partner == "CF" or nit_partner == "C/F") and factura.partner_id.documento_personal_identificacion == False:
                        raise UserError('Según acuerdo gubernativo 12-2023 las ventas de Q2 mil 500 en adelante, deben tener NIT, DPI o Pasaporte para poder emitir la factura')


                datos_receptor = {
                    "CorreoReceptor": factura.partner_id.email or "",
                    "NombreReceptor": factura.partner_id.name
                }

                #VERIFICAMOS SI SE FACTURA CON NIT O DPI
                if factura.partner_id.documento_personal_identificacion == False:
                    datos_receptor['IDReceptor'] = str(nit_partner)
                if (nit_partner == "CF" or nit_partner == "C/F") and factura.partner_id.documento_personal_identificacion:
                    datos_receptor['IDReceptor'] = str(factura.partner_id.documento_personal_identificacion)
                    datos_receptor['TipoEspecial'] = "CUI"
                elif factura.partner_id.pasaporte:
                    datos_receptor['IDReceptor'] = str(factura.partner_id.pasaporte)
                    datos_receptor['TipoEspecial'] = "EXT"
                else:
                    datos_receptor['IDReceptor'] = str(nit_partner)

                # Ajuste si es una FACTURA y la moneda es diferente a la de la compañía
                if tipo == 'FACT' and factura.currency_id != factura.company_id.currency_id:
                    datos_receptor['IDReceptor'] = "CF"

                # Creamos los TAGS necesarios
                GTDocumento = etree.Element(DTE_NS+"GTDocumento", {attr_qname: 'http://www.sat.gob.gt/dte/fel/0.1.0'}, Version="0.1", nsmap=NSMAP)
                TagSAT = etree.SubElement(GTDocumento,DTE_NS+"SAT",ClaseDocumento="dte")
                TagDTE = etree.SubElement(TagSAT,DTE_NS+"DTE",ID="DatosCertificados")
                TagDatosEmision = etree.SubElement(TagDTE,DTE_NS+"DatosEmision",ID="DatosEmision")
                TagDatosGenerales = etree.SubElement(TagDatosEmision,DTE_NS+"DatosGenerales",datos_generales)
                # Datos de emisor
                TagEmisor = etree.SubElement(TagDatosEmision,DTE_NS+"Emisor",datos_emisor)
                TagDireccionEmisor = etree.SubElement(TagEmisor,DTE_NS+"DireccionEmisor",{})
                TagDireccion = etree.SubElement(TagDireccionEmisor,DTE_NS+"Direccion",{})
                TagDireccion.text = str(factura.journal_id.direccion_id.street)+(" "+str(factura.journal_id.direccion_id.street2) if factura.journal_id.direccion_id.street2 else "" )
                TagCodigoPostal = etree.SubElement(TagDireccionEmisor,DTE_NS+"CodigoPostal",{})
                TagCodigoPostal.text = str(factura.journal_id.direccion_id.zip)
                TagMunicipio = etree.SubElement(TagDireccionEmisor,DTE_NS+"Municipio",{})
                TagMunicipio.text = str(factura.journal_id.direccion_id.city) if factura.journal_id.direccion_id.city else "Guatemala"
                TagDepartamento = etree.SubElement(TagDireccionEmisor,DTE_NS+"Departamento",{})
                TagDepartamento.text = str(factura.journal_id.direccion_id.state_id.name) if factura.journal_id.direccion_id.state_id else "Guatemala"
                TagPais = etree.SubElement(TagDireccionEmisor,DTE_NS+"Pais",{})
                TagPais.text = "GT"
                # Datos de receptor
                TagReceptor = etree.SubElement(TagDatosEmision,DTE_NS+"Receptor",datos_receptor)
                TagDireccionReceptor = etree.SubElement(TagReceptor,DTE_NS+"DireccionReceptor",{})
                TagReceptorDireccion = etree.SubElement(TagDireccionReceptor,DTE_NS+"Direccion",{})
                TagReceptorDireccion.text = (factura.partner_id.street or "Ciudad")+" "+(factura.partner_id.street2 or "")
                TagReceptorCodigoPostal = etree.SubElement(TagDireccionReceptor,DTE_NS+"CodigoPostal",{})
                TagReceptorCodigoPostal.text = factura.partner_id.zip or '01001'
                TagReceptorMunicipio = etree.SubElement(TagDireccionReceptor,DTE_NS+"Municipio",{})
                TagReceptorMunicipio.text = factura.partner_id.city or 'Guatemala'
                TagReceptorDepartamento = etree.SubElement(TagDireccionReceptor,DTE_NS+"Departamento",{})
                TagReceptorDepartamento.text = factura.partner_id.state_id.name or 'Guatemala'
                TagReceptorPais = etree.SubElement(TagDireccionReceptor,DTE_NS+"Pais",{})
                TagReceptorPais.text = "GT"
                # Frases

                data_frase = {
                    "xmlns:dte": "http://www.sat.gob.gt/dte/fel/0.2.0"
                }


                NSMAPFRASE = {
                    "dte": "http://www.sat.gob.gt/dte/fel/0.2.0"
                }

                lineas_sin_impuestos = self.verificar_lineas_sin_impuestos(factura.invoice_line_ids)
                logging.warning('lineas_sin_impuestos')
                logging.warning(lineas_sin_impuestos)
                #segun fel Versión 1.7.3 no es necesaio frases ni codigos para FESP
                if tipo != 'FESP' and factura.company_id.fel_frase_ids:
                    TagFrases = etree.SubElement(TagDatosEmision, DTE_NS + "Frases", {}, nsmap=NSMAPFRASE)

                    for frase in factura.company_id.fel_frase_ids:
                        frase_tipo = int(frase.frase)
                
                        # Excluir tipo 5 (ley de incentivos), y tipo 4 si no hay líneas sin impuestos (excepto para NCRE)
                        if frase_tipo == 5:
                            continue
                        if frase_tipo == 4 and not lineas_sin_impuestos and tipo != "NCRE":
                            continue
                        if frase_tipo == 4 and lineas_sin_impuestos and tipo == "NCRE":
                            continue  # No incluir tipo 4 en NCRE con líneas sin impuesto

                        frases_datos = {
                            "CodigoEscenario": frase.codigo,
                            "TipoFrase": frase.frase
                        }

                        TagFrase = etree.SubElement(TagFrases, DTE_NS + "Frase", frases_datos)
                        
                    #frases_datos2 =  {"CodigoEscenario": "1","TipoFrase": "2"}
                    #logging.warning('FRASES 2')
                    #logging.warning(frases_datos2)
                    # TagFrase2 = etree.SubElement(TagFrases,DTE_NS+"Frase",frases_datos2)


                # LO CAMBIAMOS POR LO DE ARRIBA EL 27 DE JUNIO DEL 2022  linea 178
                # if tipo not in  ['NDEB', 'NCRE','NABN','FESP']:
                #     TagFrases = etree.SubElement(TagDatosEmision,DTE_NS+"Frases", {},nsmap=NSMAPFRASE)
                #     for linea_frase in factura.company_id.fel_frase_ids:
                #         frases_datos = {}
                #         if tipo == 'FACT' and factura.currency_id !=  factura.company_id.currency_id:
                #             if linea_frase.frase:
                #                 frases_datos = {"CodigoEscenario": linea_frase.codigo,"TipoFrase":linea_frase.frase}
                #             else:
                #                 frases_datos = {"CodigoEscenario": linea_frase.codigo}
                #         if tipo == 'FACT' and factura.currency_id ==  factura.company_id.currency_id:
                #             if int(linea_frase.frase) == 4:
                #                 continue
                #             else:
                #                 frases_datos = {"CodigoEscenario": linea_frase.codigo,"TipoFrase":linea_frase.frase}
                #
                #         TagFrase = etree.SubElement(TagFrases,DTE_NS+"Frase",frases_datos)
                #


                # Items
                TagItems = etree.SubElement(TagDatosEmision,DTE_NS+"Items",{})

                impuestos_dic = {'IVA': 0}
                tax_iva = False
                # monto_gravable_iva = 0
                # monto_impuesto_iva = 0
                total_factura_general = 0
                total_retencion_iva = 0
                total_retencion_isr_fesp = 0
                total_retencion_isr = 0

                # new feature for support global discount
                # AJUSTE: no se envian lineas negativas como item FEL.
                # Se redistribuyen como descuento sobre las lineas positivas,
                # manteniendo Precio, Descuento, MontoGravable, MontoImpuesto,
                # Total y GranTotal con la misma base de calculo para evitar
                # errores FEL-GUI-24 / FEL-GUI-25 de SAT.
                lineas_negativas = factura.invoice_line_ids.filtered(lambda l: l.price_unit < 0)
                total_descuento_global = sum(abs(l.price_total) for l in lineas_negativas)

                reorder_lines_ids = sorted(
                    factura.invoice_line_ids.filtered(lambda l: l.price_unit > 0),
                    key=lambda x: x.price_total,
                    reverse=True
                )

                numero_linea = 1
                total_descuento_aplicado = 0.0
                total_xml = 0.0
                total_impuesto_xml = 0.0

                for linea in reorder_lines_ids:
                    iva_fespecial = 0.0

                    if not linea.product_id:
                        continue

                    tax_ids = linea.tax_ids
                    bien_servicio = "S" if linea.product_id.type == 'service' else "B"
                    linea_datos = {
                        "BienOServicio": bien_servicio,
                        "NumeroLinea": str(numero_linea)
                    }
                    numero_linea += 1

                    TagItem = etree.SubElement(TagItems, DTE_NS + "Item", linea_datos)
                    cantidad = linea.quantity or 1.0
                    unidad_medida = "UNI"

                    descripcion = linea.name
                    if factura.journal_id.descripcion_factura:
                        descripcion = linea.name
                    if factura.journal_id.producto_descripcion:
                        descripcion = str(linea.product_id.name) + ' ' + str(linea.name)

                    precio_unitario = linea.price_unit
                    precio = precio_unitario * cantidad
                    total_factura_general += precio

                    # Descuento propio de la linea en Odoo.
                    descuento_linea = 0.0
                    if linea.discount > 0:
                        descuento_linea = precio * (linea.discount / 100.0)

                    # Descuento global generado por lineas negativas.
                    descuento_global_linea = 0.0
                    pendiente_descuento = total_descuento_global - total_descuento_aplicado
                    if pendiente_descuento > 0:
                        disponible_linea = max(precio - descuento_linea, 0.0)
                        descuento_global_linea = min(disponible_linea, pendiente_descuento)
                        total_descuento_aplicado += descuento_global_linea

                    descuento = round(descuento_linea + descuento_global_linea, 6)
                    precio_menos_descuento = round(precio - descuento, 6)
                    precio_unitario_para_impuesto = precio_menos_descuento / cantidad if cantidad else 0.0

                    TagCantidad = etree.SubElement(TagItem, DTE_NS + "Cantidad", {})
                    TagCantidad.text = '{:.2f}'.format(cantidad)

                    TagUnidadMedida = etree.SubElement(TagItem, DTE_NS + "UnidadMedida", {})
                    TagUnidadMedida.text = str(unidad_medida)

                    TagDescripcion = etree.SubElement(TagItem, DTE_NS + "Descripcion", {})
                    if factura.journal_id.columna_extra_fel_py:
                        logging.warning('si hay py')
                        exec(factura.journal_id.columna_extra_fel_py)
                    else:
                        TagDescripcion.text = (str(linea.name) + '|' + str(linea.product_id.default_code)) if linea.product_id.default_code else descripcion

                    TagPrecioUnitario = etree.SubElement(TagItem, DTE_NS + "PrecioUnitario", {})
                    TagPrecioUnitario.text = '{:.6f}'.format(precio_unitario)

                    TagPrecio = etree.SubElement(TagItem, DTE_NS + "Precio", {})
                    TagPrecio.text = '{:.6f}'.format(precio)

                    TagDescuento = etree.SubElement(TagItem, DTE_NS + "Descuento", {})
                    TagDescuento.text = '{:.6f}'.format(descuento)

                    if tipo != 'NABN':
                        TagImpuestos = etree.SubElement(TagItem, DTE_NS + "Impuestos", {})

                        currency = linea.move_id.currency_id
                        taxes = tax_ids.compute_all(
                            precio_unitario_para_impuesto,
                            currency,
                            cantidad,
                            linea.product_id,
                            linea.move_id.partner_id
                        )

                        if len(taxes['taxes']) > 0:
                            for impuesto in taxes['taxes']:
                                if impuesto['name'] == 'ISR FACTURA ESPECIAL':
                                    total_retencion_isr_fesp += impuesto['amount']

                                elif impuesto['name'] == 'IVA por Pagar' or impuesto['name'] == 'IVA FACTURA ESPECIAL':
                                    valor_impuesto = impuesto['amount']
                                    base_imponible = impuesto['base']
                                    nombre_impuesto = "IVA"
                                    tax_iva = True

                                    total_impuesto_xml += valor_impuesto
                                    lista_impuestos.append({
                                        'nombre': nombre_impuesto,
                                        'monto': valor_impuesto
                                    })

                                    TagImpuesto = etree.SubElement(TagImpuestos, DTE_NS + "Impuesto", {})
                                    TagNombreCorto = etree.SubElement(TagImpuesto, DTE_NS + "NombreCorto", {})
                                    TagNombreCorto.text = nombre_impuesto

                                    TagCodigoUnidadGravable = etree.SubElement(TagImpuesto, DTE_NS + "CodigoUnidadGravable", {})
                                    TagCodigoUnidadGravable.text = "1"

                                    TagMontoGravable = etree.SubElement(TagImpuesto, DTE_NS + "MontoGravable", {})
                                    TagMontoGravable.text = "{:.6f}".format(base_imponible)

                                    TagMontoImpuesto = etree.SubElement(TagImpuesto, DTE_NS + "MontoImpuesto", {})
                                    TagMontoImpuesto.text = "{:.6f}".format(valor_impuesto)

                                    iva_fespecial += valor_impuesto

                                elif impuesto['name'] == 'IVA RETENCION FACTURA ESPECIAL':
                                    total_retencion_iva += impuesto['amount']
                        else:
                            TagImpuesto = etree.SubElement(TagImpuestos, DTE_NS + "Impuesto", {})
                            TagNombreCorto = etree.SubElement(TagImpuesto, DTE_NS + "NombreCorto", {})
                            TagNombreCorto.text = "IVA"

                            TagCodigoUnidadGravable = etree.SubElement(TagImpuesto, DTE_NS + "CodigoUnidadGravable", {})
                            TagCodigoUnidadGravable.text = "2"

                            TagMontoGravable = etree.SubElement(TagImpuesto, DTE_NS + "MontoGravable", {})
                            TagMontoGravable.text = "{:.6f}".format(precio_menos_descuento)

                            TagMontoImpuesto = etree.SubElement(TagImpuesto, DTE_NS + "MontoImpuesto", {})
                            TagMontoImpuesto.text = "0.000000"

                    if (tipo in ['FACT', 'NCRE']) and factura.currency_id != factura.company_id.currency_id:
                        if tipo == 'NABN':
                            TagImpuestos = etree.SubElement(TagItem, DTE_NS + "Impuestos", {})

                        TagImpuesto = etree.SubElement(TagImpuestos, DTE_NS + "Impuesto", {})
                        TagNombreCorto = etree.SubElement(TagImpuesto, DTE_NS + "NombreCorto", {})
                        TagNombreCorto.text = "IVA"

                        TagCodigoUnidadGravable = etree.SubElement(TagImpuesto, DTE_NS + "CodigoUnidadGravable", {})
                        TagCodigoUnidadGravable.text = "2"

                        TagMontoGravable = etree.SubElement(TagImpuesto, DTE_NS + "MontoGravable", {})
                        TagMontoGravable.text = "{:.6f}".format(precio_menos_descuento)

                        TagMontoImpuesto = etree.SubElement(TagImpuesto, DTE_NS + "MontoImpuesto", {})
                        TagMontoImpuesto.text = "0.000000"

                    TagTotal = etree.SubElement(TagItem, DTE_NS + "Total", {})
                    if tipo == 'FESP':
                        total_linea_fesp = precio_menos_descuento
                        TagTotal.text = '{:.6f}'.format(total_linea_fesp)
                        total_xml += total_linea_fesp
                    else:
                        TagTotal.text = '{:.6f}'.format(precio_menos_descuento)
                        total_xml += precio_menos_descuento

                TagTotales = etree.SubElement(TagDatosEmision, DTE_NS + "Totales", {})
                if tipo != 'NABN':
                    TagTotalImpuestos = etree.SubElement(TagTotales, DTE_NS + "TotalImpuestos", {})

                    if len(lista_impuestos) > 0:
                        dato_impuesto = {
                            'NombreCorto': 'IVA',
                            'TotalMontoImpuesto': '{:.6f}'.format(total_impuesto_xml)
                        }
                        etree.SubElement(TagTotalImpuestos, DTE_NS + "TotalImpuesto", dato_impuesto)
                    else:
                        dato_impuesto = {
                            'NombreCorto': "IVA",
                            'TotalMontoImpuesto': "0.000000"
                        }
                        etree.SubElement(TagTotalImpuestos, DTE_NS + "TotalImpuesto", dato_impuesto)

                TagGranTotal = etree.SubElement(TagTotales, DTE_NS + "GranTotal", {})
                TagGranTotal.text = '{:.6f}'.format(factura.currency_id.round(total_xml))

                if tipo == 'FACT' and factura.currency_id !=  factura.company_id.currency_id and factura.tipo_factura == "exportacion":
                    dato_impuesto = {'NombreCorto': "IVA",'TotalMontoImpuesto': str(0.00)}
                    TagTotalImpuesto = etree.SubElement(TagTotalImpuestos,DTE_NS+"TotalImpuesto",dato_impuesto)
                    TagComplementos = etree.SubElement(TagDatosEmision,DTE_NS+"Complementos",{})
                    datos_complementos = {
                        "IDComplemento": "EXPORTACION",
                        "NombreComplemento": "EXPORTACION",
                        "URIComplemento": "EXPORTACION"
                    }
                    TagComplemento = etree.SubElement(TagComplementos,DTE_NS+"Complemento",datos_complementos)
                    NSMAP = {
                        "cex": "http://www.sat.gob.gt/face2/ComplementoExportaciones/0.1.0"
                    }
                    cex = "{http://www.sat.gob.gt/face2/ComplementoExportaciones/0.1.0}"

                    TagExportacion = etree.SubElement(TagComplemento,cex+"Exportacion",{},Version="1",nsmap=NSMAP)
                    TagNombreConsignatarioODestinatario = etree.SubElement(TagExportacion,cex+"NombreConsignatarioODestinatario",{})
                    TagNombreConsignatarioODestinatario.text = str(factura.partner_id.name)
                    TagDireccionConsignatarioODestinatario = etree.SubElement(TagExportacion,cex+"DireccionConsignatarioODestinatario",{})
                    TagDireccionConsignatarioODestinatario.text = str(factura.company_id.street or "")+(" " + str(factura.company_id.street2) if factura.company_id.street2 else '' )
                    TagCodigoConsignatarioODestinatario = etree.SubElement(TagExportacion,cex+"CodigoConsignatarioODestinatario",{})
                    TagCodigoConsignatarioODestinatario.text = str(factura.company_id.zip or "")
                    TagNombreComprador = etree.SubElement(TagExportacion,cex+"NombreComprador",{})
                    TagNombreComprador.text = str(factura.partner_id.name)
                    TagDireccionComprador = etree.SubElement(TagExportacion,cex+"DireccionComprador",{})
                    TagDireccionComprador.text = str(factura.company_id.street or "")+(" " + str(factura.company_id.street2) if factura.company_id.street2 else '' )
                    TagCodigoComprador = etree.SubElement(TagExportacion,cex+"CodigoComprador",{})
                    TagCodigoComprador.text = str(factura.company_id.zip) if factura.company_id.zip else "N/A"
                    TagOtraReferencia = etree.SubElement(TagExportacion,cex+"OtraReferencia",{})
                    TagOtraReferencia.text = "N/A"
                    TagINCOTERM = etree.SubElement(TagExportacion,cex+"INCOTERM",{})
                    TagINCOTERM.text = str(factura.fel_incoterm)
                    TagNombreExportador = etree.SubElement(TagExportacion,cex+"NombreExportador",{})
                    TagNombreExportador.text = str(factura.company_id.name)
                    TagCodigoExportador = etree.SubElement(TagExportacion,cex+"CodigoExportador",{})
                    TagCodigoExportador.text = factura.company_id.fel_codigo_exportador if factura.company_id.fel_codigo_exportador else "N/A"


                if tipo == 'NDEB':
                    factura_original_id = self.env['account.move'].search([('name','=',factura.ref.split(':')[1].split()  )])
                    logging.warning('factura_original_id')
                    logging.warning(factura_original_id)
                    if factura_original_id and factura.currency_id.id == factura_original_id.currency_id.id:
                        logging.warn('si')
                        TagComplementos = etree.SubElement(TagDatosEmision,DTE_NS+"Complementos",{})
                        cno = "{http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0}"
                        NSMAP_REF = {"cno": "http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0"}
                        datos_complemento = {'IDComplemento': 'ReferenciasNota', 'NombreComplemento':'Nota de Debito','URIComplemento':'text'}
                        TagComplemento = etree.SubElement(TagComplementos,DTE_NS+"Complemento",datos_complemento)
                        datos_referencias = {
                            'FechaEmisionDocumentoOrigen': str(factura_original_id.invoice_date),
                            'MotivoAjuste': 'Anulación',
                            'NumeroAutorizacionDocumentoOrigen': str(factura_original_id.fel_numero_autorizacion),
                            'NumeroDocumentoOrigen': str(factura_original_id.fel_numero),
                            'SerieDocumentoOrigen': str(factura_original_id.fel_serie),
                            'Version': '0.0'
                        }
                        TagReferenciasNota = etree.SubElement(TagComplemento,cno+"ReferenciasNota",datos_referencias,nsmap=NSMAP_REF)



                if tipo == 'NCRE' or tipo == 'NABN':
                    if factura_original_id and factura.currency_id.id == factura_original_id.currency_id.id:
                        logging.warn('si')
                        TagComplementos = etree.SubElement(TagDatosEmision,DTE_NS+"Complementos",{})
                        cno = "{http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0}"
                        NSMAP_REF = {"cno": "http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0"}
                        datos_complemento = {'IDComplemento': 'Notas', 'NombreComplemento':'Notas','URIComplemento':'text'}
                        TagComplemento = etree.SubElement(TagComplementos,DTE_NS+"Complemento",datos_complemento)
                        datos_referencias = {
                            'FechaEmisionDocumentoOrigen': str(factura_original_id.invoice_date),
                            'MotivoAjuste': motivo_nc,
                            'NumeroAutorizacionDocumentoOrigen': str(factura_original_id.fel_numero_autorizacion),
                            'NumeroDocumentoOrigen': str(factura_original_id.fel_numero),
                            'SerieDocumentoOrigen': str(factura_original_id.fel_serie),
                            'Version': '0.0'
                        }
                        TagReferenciasNota = etree.SubElement(TagComplemento,cno+"ReferenciasNota",datos_referencias,nsmap=NSMAP_REF)


                if tipo == 'FCAM':
                    NSMAPFCAM = {
                        "cfc": "http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0"
                    }
                    DTE_NS_CFCAM = "{http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0}"
                    TagComplementos = etree.SubElement(TagDatosEmision,DTE_NS+"Complementos",{})
                    datos_complemento = {'IDComplemento': 'Cambiaria', 'NombreComplemento':'Cambiaria','URIComplemento':'http://www.sat.gob.gt/fel/cambiaria.xsd'}
                    TagComplemento = etree.SubElement(TagComplementos,DTE_NS+"Complemento",datos_complemento)
                    tag_datos_factura_cambiaria = {
                        'Version': '1'
                    }
                    TagAbonosFacturaCambiaria = etree.SubElement(TagComplemento,DTE_NS_CFCAM+"AbonosFacturaCambiaria",tag_datos_factura_cambiaria,nsmap=NSMAPFCAM)
                    TagAbono = etree.SubElement(TagAbonosFacturaCambiaria,DTE_NS_CFCAM+"Abono")
                    TagNumeroAbono = etree.SubElement(TagAbono,DTE_NS_CFCAM+"NumeroAbono")
                    logging.warning('numero abonos')
                    logging.warning(factura.fel_numero_abonos_fc)
                    TagNumeroAbono.text = str(factura.fel_numero_abonos_fc) if factura.fel_numero_abonos_fc > 0 else str(factura.company_id.fel_numero_abonos_fc)
                    TagFechaVencimiento = etree.SubElement(TagAbono,DTE_NS_CFCAM+"FechaVencimiento")
                    fecha_fcam = False
                    if factura.fel_fecha_vencimiento_fc:
                        fecha_fcam = datetime.datetime.strftime(factura.fel_fecha_vencimiento_fc, "%Y-%m-%d")
                    else:
                        fecha_fcam = datetime.datetime.strftime(factura.invoice_date_due, "%Y-%m-%d")

                    TagFechaVencimiento.text = fecha_fcam
                    TagMontoAbono = etree.SubElement(TagAbono,DTE_NS_CFCAM+"MontoAbono")
                    TagMontoAbono.text = str(factura.fel_monto_abonos_fc) if factura.fel_monto_abonos_fc > 0 else str(factura.amount_total)


                if tipo == 'FESP':
                    NSMAPFRASECFC = {
                        "cfe": "http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0"
                    }
                    DTE_NS_CFC = "{http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0}"
                    TagComplementos = etree.SubElement(TagDatosEmision,DTE_NS+"Complementos",{})
                    #NSMAP_REF = {"cno": "http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0"}
                    datos_complemento = {'IDComplemento': 'FacturaEspecial', 'NombreComplemento':'FacturaEspecial','URIComplemento':'http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0'}
                    TagComplemento = etree.SubElement(TagComplementos,DTE_NS+"Complemento",datos_complemento)
                    tag_datos_factura_especial = {
                        'Version': '1'
                    }

                    TagRetencionFacturaEspecial = etree.SubElement(TagComplemento,DTE_NS_CFC+"RetencionesFacturaEspecial",tag_datos_factura_especial,nsmap=NSMAPFRASECFC)
                    TagRetencionISR = etree.SubElement(TagRetencionFacturaEspecial,DTE_NS_CFC+"RetencionISR")
                    # tomamos en cuenta IVA Factura Especial para total_retencion_iva
                    TagRetencionISR.text = '{:.6f}'.format(total_retencion_isr_fesp*-1)
                    TagRetencionIVA = etree.SubElement(TagRetencionFacturaEspecial,DTE_NS_CFC+"RetencionIVA")
                    TagRetencionIVA.text = '{:.6f}'.format(total_retencion_iva*-1)
                    TagTotalMenosRetenciones = etree.SubElement(TagRetencionFacturaEspecial,DTE_NS_CFC+"TotalMenosRetenciones")
                    TagTotalMenosRetenciones.text = '{:.6f}'.format(factura.amount_total_signed*-1)

                if factura.currency_id.id != factura.company_id.currency_id.id:
                    TagAdenda = etree.SubElement(TagSAT,DTE_NS+"Adenda",{})
                    if factura.comment:
                        TagComentario = etree.SubElement(TagAdenda, DTE_NS+"Comentario",{})
                        TagComentario.text = factura.comment
                    if factura.currency_id.id != factura.company_id.currency_id.id:
                        TagNitCliente = etree.SubElement(TagAdenda, DTE_NS+"NitCliente",{})
                        if factura.partner_id.vat:
                            if '-' in factura.partner_id.vat:
                                TagNitCliente.text = factura.partner_id.vat.replace('-','')
                            else:
                                TagNitCliente.text = factura.partner_id.vat
                
                #Ejemplo de adenda, enviamos secuencia interna de odoo
                if tipo in ['FACT','NCRE','NDEB','NABN','FESP','FCAM']:
                    factura._set_next_sequence()
                    TagAdenda = etree.SubElement(TagSAT,DTE_NS+"Adenda",{})
                    TagNint = etree.SubElement(TagAdenda,DTE_NS+"NInt",{})
                    TagNint.text = factura.name
                             
                xmls = etree.tostring(GTDocumento, encoding="UTF-8")
                xmls = xmls.decode("utf-8").replace("&amp;", "&").encode("utf-8")
                xmls_base64 = base64.b64encode(xmls)
                logging.warn(xmls)


                url = "https://signer-emisores.feel.com.gt/sign_solicitud_firmas/firma_xml"

                nit_company = "CF"
                if '-' in factura.company_id.vat:
                    nit_company = factura.company_id.vat.replace('-','')
                else:
                    nit_company = factura.company_id.vat


                nuevo_json = {
                    'llave': str(factura.company_id.fel_llave_pre_firma),
                    'codigo': str(nit_company),
                    'alias': str(factura.company_id.fel_usuario),
                    'es_anulacion': 'N',
                    'archivo': xmls_base64.decode("utf-8")
                }

                nuevos_headers = {"content-type": "application/json"}
                response = requests.post(url, json = nuevo_json, headers = nuevos_headers)

                respone_json=response.json()
                logging.warning('respuesta autentic')
                logging.warning(nuevo_json)
                logging.warning(respone_json)

                if respone_json['resultado']:
                        headers = {
                            "USUARIO": str(factura.company_id.fel_usuario),
                            "LLAVE": str(factura.company_id.fel_llave_firma),
                            "IDENTIFICADOR": str(factura.journal_id.name)+'/'+str(factura.payment_reference) if factura.payment_reference else str(factura.journal_id.name)+'/'+str(factura.id),
                            "Content-Type": "application/json",
                        }

                        logging.warning('VALIDADO')
                        logging.warning(headers)

                        nit_company = "CF"
                        if '-' in factura.company_id.vat:
                            nit_company = factura.company_id.vat.replace('-','')
                        else:
                            nit_company = factura.company_id.vat
                        data = {
                            "nit_emisor": str(nit_company),
                            "correo_copia": str(factura.company_id.email),
                            "xml_dte": respone_json["archivo"]
                        }

                        r = requests.post("https://certificador.feel.com.gt/fel/certificacion/v2/dte/", json=data, headers=headers)
                        retorno_certificacion_json = r.json()
                        logging.warn(retorno_certificacion_json)
                        if retorno_certificacion_json['resultado']:
                            factura.fel_numero_autorizacion = retorno_certificacion_json["uuid"]
                            # factura.name = str(retorno_certificacion_json["serie"])+"/"+str(retorno_certificacion_json["numero"])
                            factura.fel_serie = retorno_certificacion_json["serie"]
                            factura.fel_numero = retorno_certificacion_json["numero"]
                            factura.fel_documento_certificado = "https://report.feel.com.gt/ingfacereport/ingfacereport_documento?uuid="+retorno_certificacion_json["uuid"]
                        else:
                            raise UserError(str(retorno_certificacion_json))
                else:
                    raise UserError(str(respone_json))

        return super(AccountMove, self)._post()



    def button_draft(self):
        for factura in self:
            if factura.fel_serie and factura.fel_numero and factura.fel_numero_autorizacion and factura.company_id.fel_llave_firma:
                attr_qname = etree.QName("http://www.w3.org/2001/XMLSchema-instance", "schemaLocation")
                DTE_NS = "{http://www.sat.gob.gt/dte/fel/0.1.0}"
                # Nuevo SMAP
                NSMAP = {
                    "ds": "http://www.w3.org/2000/09/xmldsig#",
                    "dte": "http://www.sat.gob.gt/dte/fel/0.1.0",
                    "xsi": "http://www.w3.org/2001/XMLSchema-instance"
                }
                tipo = factura.journal_id.fel_tipo_dte
                GTAnulacionDocumento = etree.Element(DTE_NS+"GTAnulacionDocumento", {attr_qname: 'http://www.sat.gob.gt/dte/fel/0.1.0'}, Version="0.1", nsmap=NSMAP)
                datos_sat = {'ClaseDocumento': 'dte'}
                TagSAT = etree.SubElement(GTAnulacionDocumento,DTE_NS+"SAT",{})
                # dato_anulacion = {'ID': 'DatosCertificados'}
                dato_anulacion = {"ID": "DatosCertificados"}
                TagAnulacionDTE = etree.SubElement(TagSAT,DTE_NS+"AnulacionDTE",dato_anulacion)
                fecha_factura = self.fecha_hora_factura(factura.invoice_date)
                fecha_anulacion = datetime.datetime.strftime(fields.Datetime.context_timestamp(self, datetime.datetime.now()), "%Y-%m-%d")
                hora_anulacion = datetime.datetime.strftime(fields.Datetime.context_timestamp(self, datetime.datetime.now()), "%H:%M:%S")
                fecha_anulacion = str(fecha_anulacion)+'T'+str(hora_anulacion)
                nit_partner = "CF"
                if factura.partner_id.vat:
                    logging.warn('si nit')
                    if ('-' in factura.partner_id.vat):
                        logging.warn('si nit if')
                        nit_partner = factura.partner_id.vat.replace('-','')
                    else:
                        nit_partner = factura.partner_id.vat
                        logging.warn('si nit else')


                nit_company = "CF"
                if factura.journal_id.direccion_id.vat and ('-' in factura.journal_id.direccion_id.vat):
                    nit_company = factura.company_id.vat.replace('-','')
                else:
                    nit_company = factura.company_id.vat

                datos_generales = {
                    "ID": "DatosAnulacion",
                    "NumeroDocumentoAAnular": str(factura.fel_numero_autorizacion),
                    "NITEmisor": str(nit_company),
                    "IDReceptor": str(nit_partner),
                    "FechaEmisionDocumentoAnular": fecha_factura,
                    "FechaHoraAnulacion": fecha_anulacion,
                    "MotivoAnulacion": "Anulacion factura"
                }
                if tipo == 'FACT' and (factura.currency_id.id !=  factura.company_id.currency_id.id):
                    datos_generales['IDReceptor'] = "CF"
                TagDatosGenerales = etree.SubElement(TagAnulacionDTE,DTE_NS+"DatosGenerales",datos_generales)


                xmls = etree.tostring(GTAnulacionDocumento, encoding="UTF-8")
                logging.warn('xmls')
                logging.warn(xmls)
                xmls = xmls.decode("utf-8").replace("&amp;", "&").encode("utf-8")
                xmls_base64 = base64.b64encode(xmls)
                logging.warn(xmls_base64)
                logging.warn('BASE 64')
                logging.warn(xmls_base64.decode("utf-8"))


                url = "https://signer-emisores.feel.com.gt/sign_solicitud_firmas/firma_xml"

                nuevo_json = {
                    "llave": factura.company_id.fel_llave_pre_firma,
                    "archivo": xmls_base64.decode("utf-8"),
                    "codigo": str(factura.company_id.vat),
                    "alias": str(factura.company_id.fel_usuario),
                    "es_anulacion": "S"
                }
                logging.warn('NUEVO JSON ARCHIVO')
                logging.warn(xmls_base64.decode("utf-8"))

                nuevos_headers = {"content-type": "application/json"}
                response = requests.post(url, json = nuevo_json, headers = nuevos_headers)
                respone_json=response.json()
                logging.warn('RESPONSE JSON')
                logging.warn(respone_json)
                if respone_json['resultado']:


                    headers = {
                        "USUARIO": str(factura.company_id.fel_usuario),
                        "LLAVE": factura.company_id.fel_llave_firma,
                        "IDENTIFICADOR": str(factura.journal_id.name)+'/'+str(factura.id)+'/'+'ANULACION',
                        "Content-Type": "application/json",
                    }
                    data = {
                        "nit_emisor": factura.company_id.vat,
                        "correo_copia": factura.company_id.email,
                        "xml_dte": respone_json["archivo"]
                    }

                    r = requests.post("https://certificador.feel.com.gt/fel/anulacion/v2/dte/", json=data, headers=headers)
                    logging.warn(r.json())
                    retorno_certificacion_json = r.json()
                    logging.warn('si anuló')
                    if not retorno_certificacion_json['resultado']:
                        raise UserError(str('ERROR AL ANULAR'))
                else:
                    raise UserError(str('ERROR AL ANULAR'))

        return super(AccountMove, self).button_draft()
