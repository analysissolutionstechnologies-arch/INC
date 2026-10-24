# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import time
import xlsxwriter
import base64
import io
import logging

class AsistenteReporteCompras(models.TransientModel):
    _name = 'l10n_gt_extra.asistente_reporte_compras'

    diarios_id = fields.Many2many("account.journal", string="Diarios", required=True)
    impuesto_id = fields.Many2one("account.tax", string="Impuesto", required=True)
    folio_inicial = fields.Integer(string="Folio Inicial", required=True, default=1)
    fecha_desde = fields.Date(string="Fecha Inicial", required=True, default=lambda self: time.strftime('%Y-%m-01'))
    fecha_hasta = fields.Date(string="Fecha Final", required=True, default=lambda self: time.strftime('%Y-%m-%d'))
    name = fields.Char('Nombre archivo', size=32)
    archivo = fields.Binary('Archivo', filters='.xls')

    def print_report(self):
        data = {
             'ids': [],
             'model': 'l10n_gt_extra.asistente_reporte_compras',
             'form': self.read()[0]
        }
        return self.env.ref('l10n_gt_extra.action_reporte_compras').with_context(landscape=True).report_action(self, data=data)

    def print_report_excel(self):
        for w in self:
            dict = {}
            dict['fecha_hasta'] = w['fecha_hasta']
            dict['fecha_desde'] = w['fecha_desde']
            dict['impuesto_id'] = [w.impuesto_id.id, w.impuesto_id.name]
            dict['diarios_id'] =[x.id for x in w.diarios_id]

            res = self.env['report.l10n_gt_extra.reporte_compras'].lineas(dict)
            lineas = res['lineas']
            totales = res['totales']

            f = io.BytesIO()
            libro = xlsxwriter.Workbook(f)
            hoja = libro.add_worksheet('Reporte')
            formato_fecha = libro.add_format({'num_format': 'dd/mm/yy'})
            formato_titulos = libro.add_format({
                'bold': 1,
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'fg_color': '#ddebf7',
                'font_color': "black",
                'text_wrap': False,
                'center_across': True})
            
            formato_subtitulos = libro.add_format({
                'bold': 1,
                'border': 0,
                'align': 'left',
                'font_color': "black",
                'text_wrap': False})
            
            formato_normal = libro.add_format({
                'align': 'center',
                'text_wrap': False})

            hoja.write(0, 0, 'LIBRO DE COMPRAS Y SERVICIOS', formato_titulos)
            hoja.write(2, 0, 'NUMERO DE IDENTIFICACION TRIBUTARIA', formato_subtitulos)
            hoja.write(2, 1, w.diarios_id[0].company_id.partner_id.vat)
            hoja.write(3, 0, 'NOMBRE COMERCIAL', formato_subtitulos)
            hoja.write(3, 1, w.diarios_id[0].company_id.partner_id.name)
            hoja.write(2, 3, 'DOMICILIO FISCAL', formato_subtitulos)
            hoja.write(2, 4, w.diarios_id[0].company_id.partner_id.street)
            hoja.write(3, 3, 'REGISTRO DEL', formato_subtitulos)
            hoja.write(3, 4, w.fecha_desde, formato_fecha)
            hoja.write(3, 5, 'AL',formato_subtitulos)
            hoja.write(3, 6, w.fecha_hasta, formato_fecha)

            y = 5
            hoja.write(y, 0, 'TIPO', formato_titulos)
            hoja.write(y, 1, 'FECHA', formato_titulos)
            hoja.write(y, 2, 'SERIE', formato_titulos)   
            hoja.write(y, 3, 'NUMERO', formato_titulos)
            hoja.write(y, 4, 'PROVEEDOR', formato_titulos)
            hoja.write(y, 5, 'NIT', formato_titulos)
            hoja.write(y, 6, 'COMPRAS', formato_titulos)
            hoja.write(y, 7, 'COMPRAS EXENTO', formato_titulos)
            hoja.write(y, 8, 'SERVICIOS', formato_titulos)
            hoja.write(y, 9, 'SERVICIOS EXENTO', formato_titulos)
            hoja.write(y, 10, 'COMBUSTIBLE', formato_titulos)
            hoja.write(y, 11, 'COMBUSTIBLE EXENTO', formato_titulos)
            hoja.write(y, 12, 'IMPORTACIONES', formato_titulos)
            hoja.write(y, 13, 'PEQUEÑOS CONTRIBUYENTES', formato_titulos)
            hoja.write(y, 14, 'IVA', formato_titulos)
            hoja.write(y, 15, 'TOTAL', formato_titulos)

            for linea in lineas:
                y += 1
                hoja.write(y, 0, linea['tipo'], formato_normal)
                hoja.write(y, 1, linea['fecha'], formato_fecha)
                hoja.write(y, 2, linea['serie'], formato_normal)
                hoja.write(y, 3, linea['numero'], formato_normal)
                hoja.write(y, 4, linea['proveedor']['name'], formato_normal)
                hoja.write(y, 5, linea['proveedor']['vat'], formato_normal)
                hoja.write(y, 6, linea['compra'], formato_normal)
                hoja.write(y, 7, linea['compra_exento'], formato_normal)
                hoja.write(y, 8, linea['servicio'], formato_normal)
                hoja.write(y, 9, linea['servicio_exento'], formato_normal)
                hoja.write(y, 10, linea['combustible'], formato_normal)
                hoja.write(y, 11, linea['combustible_exento'], formato_normal)
                hoja.write(y, 12, linea['importacion'] + linea['importacion_exento'], formato_normal)
                hoja.write(y, 13, linea['pequeño'] + linea['pequeño_exento'], formato_normal)
                hoja.write(y, 14, linea['iva'], formato_normal)
                hoja.write(y, 15, linea['total'], formato_normal)

            y += 1
            hoja.write(y, 3, 'Totales', formato_normal)
            hoja.write(y, 5, totales['compra']['neto'], formato_normal)
            hoja.write(y, 6, totales['compra']['exento'], formato_normal)
            hoja.write(y, 7, totales['servicio']['neto'], formato_normal)
            hoja.write(y, 8, totales['servicio']['exento'], formato_normal)
            hoja.write(y, 9, totales['combustible']['neto'], formato_normal)
            hoja.write(y, 10, totales['combustible']['exento'],formato_normal)
            hoja.write(y, 11, totales['importacion']['neto'] + totales['importacion']['exento'], formato_normal)
            hoja.write(y, 12, totales['pequeño']['neto'] + totales['pequeño']['exento'], formato_normal)
            hoja.write(y, 13, totales['compra']['iva'] + totales['servicio']['iva'] + totales['combustible']['iva'] + totales['importacion']['iva'] + totales['pequeño']['iva'], formato_normal)
            hoja.write(y, 14, totales['compra']['total'] + totales['servicio']['total'] + totales['combustible']['total'] + totales['importacion']['total'] + totales['pequeño']['total'], formato_normal)

            y += 2
            hoja.write(y, 0, 'CANTIDAD DE FACTURAS', formato_subtitulos)
            hoja.write(y, 1, totales['num_facturas'])
            y += 1
            hoja.write(y, 0, 'TOTAL DEBITO FISCAL',formato_subtitulos)
            hoja.write(y, 1, totales['compra']['iva'] + totales['servicio']['iva'] + totales['combustible']['iva'] + totales['importacion']['iva'] + totales['pequeño']['iva'])

            y += 2
            hoja.write(y, 3, 'EXENTO', formato_subtitulos)
            hoja.write(y, 4, 'NETO', formato_subtitulos)
            hoja.write(y, 5, 'IVA', formato_subtitulos)
            hoja.write(y, 6, 'TOTAL',formato_subtitulos)
            y += 1
            hoja.write(y, 1, 'COMPRAS')
            hoja.write(y, 3, totales['compra']['exento'])
            hoja.write(y, 4, totales['compra']['neto'])
            hoja.write(y, 5, totales['compra']['iva'])
            hoja.write(y, 6, totales['compra']['total'])
            y += 1
            hoja.write(y, 1, 'SERVICIOS')
            hoja.write(y, 3, totales['servicio']['exento'])
            hoja.write(y, 4, totales['servicio']['neto'])
            hoja.write(y, 5, totales['servicio']['iva'])
            hoja.write(y, 6, totales['servicio']['total'])
            y += 1
            hoja.write(y, 1, 'COMBUSTIBLES')
            hoja.write(y, 3, totales['combustible']['exento'])
            hoja.write(y, 4, totales['combustible']['neto'])
            hoja.write(y, 5, totales['combustible']['iva'])
            hoja.write(y, 6, totales['combustible']['total'])
            y += 1
            hoja.write(y, 1, 'IMPORTACIONES')
            hoja.write(y, 3, totales['importacion']['exento'])
            hoja.write(y, 4, totales['importacion']['neto'])
            hoja.write(y, 5, totales['importacion']['iva'])
            hoja.write(y, 6, totales['importacion']['total'])
            y += 1
            hoja.write(y, 1, 'PEQUEÑOS CONTRIBUYENTES')
            hoja.write(y, 3, totales['pequeño']['exento'])
            hoja.write(y, 4, totales['pequeño']['neto'])
            hoja.write(y, 5, totales['pequeño']['iva'])
            hoja.write(y, 6, totales['pequeño']['total'])
            y += 1
            hoja.write(y, 1, 'TOTALES')
            hoja.write(y, 3, totales['compra']['exento']+totales['servicio']['exento']+totales['combustible']['exento']+totales['importacion']['exento']+totales['pequeño']['exento'])
            hoja.write(y, 4, totales['compra']['neto']+totales['servicio']['neto']+totales['combustible']['neto']+totales['importacion']['neto']+totales['pequeño']['neto'])
            hoja.write(y, 5, totales['compra']['iva']+totales['servicio']['iva']+totales['combustible']['iva']+totales['importacion']['iva']+totales['pequeño']['iva'])
            hoja.write(y, 6, totales['compra']['total']+totales['servicio']['total']+totales['combustible']['total']+totales['importacion']['total']+totales['pequeño']['total'])

            libro.close()
            datos = base64.b64encode(f.getvalue())
            self.write({'archivo':datos, 'name':'libro_de_compras.xlsx'})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'l10n_gt_extra.asistente_reporte_compras',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
