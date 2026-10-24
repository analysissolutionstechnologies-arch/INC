# -*- coding: utf-8 -*-
import io
import xlsxwriter
from werkzeug.exceptions import Forbidden
from odoo import http, fields
from odoo.http import request


class IncmdActivosExcelController(http.Controller):

    @http.route('/incmd_activos/export_xlsx', type='http', auth='user')
    def export_xlsx(self, **kwargs):
        if not request.env.user.has_group('incmd_activos.group_incmd_activos_manager'):
            raise Forbidden()

        Activo = request.env['incmd.activo'].sudo()
        activos = Activo.search([], order='location_id, department_id, responsible_employee_id, name')

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Activos')

        title_format = workbook.add_format({'bold': True, 'font_size': 14})
        header_format = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#D9EAF7'})
        text_format = workbook.add_format({'border': 1})

        worksheet.merge_range('A1:F1', 'Reporte de Activos Fijos', title_format)
        worksheet.write('A2', 'Fecha de generación')
        worksheet.write('B2', fields.Datetime.context_timestamp(request.env.user, fields.Datetime.now()).strftime('%d/%m/%Y %H:%M'))

        headers = ['Ubicación', 'Departamento', 'Persona Responsable', 'Genérico', 'Marca', 'Modelo']
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, header_format)

        row = 4
        for activo in activos:
            worksheet.write(row, 0, activo.location_id.display_name or '', text_format)
            worksheet.write(row, 1, activo.department_id.name or '', text_format)
            worksheet.write(row, 2, activo.responsible_employee_id.name or '', text_format)
            worksheet.write(row, 3, activo.generic or '', text_format)
            worksheet.write(row, 4, activo.brand or '', text_format)
            worksheet.write(row, 5, activo.model or '', text_format)
            row += 1

        worksheet.set_column(0, 0, 35)
        worksheet.set_column(1, 1, 25)
        worksheet.set_column(2, 2, 30)
        worksheet.set_column(3, 5, 22)
        workbook.close()
        output.seek(0)

        filename = 'reporte_activos_fijos.xlsx'
        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', http.content_disposition(filename)),
            ]
        )
