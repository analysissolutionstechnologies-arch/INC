# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_validate_ticket_attachment(self):
        for record in self:
            # Evitar duplicados
            if not record.x_x_studio_adjuntos_pedido_ir_attachment_count > 0:
                raise UserError("No se encontró ningún archivo adjunto para este pedido. Por favor, adjunte un archivo antes de generar el ticket.")
            ticket = self.env['project.task'].search([('x_studio_pedido', '=', record.id)], limit=1)
            if ticket:
                raise UserError("Ya existe un ticket generado para este pedido. No se puede generar otro.")

            if record.state == 'draft':
                for line in record.order_line:
                    if line.product_id.x_studio_es_moto_1:

                        # Buscar adjunto
                        attachment = self.env['ir.attachment'].search([
                            ('res_model', '=', 'sale.order.line'),
                            ('res_id', '=', line.id),
                            ('name', '=', line.x_studio_adjunto)
                        ], limit=1)

                        # Construir el enlace al archivo adjunto
                        attachment_link = ''
                        if attachment:
                            # URL para descargar el archivo
                            attachment_link = f'<a href="/web/content/{attachment.id}/{attachment.name}" target="_blank">Descargar Adjunto</a>'

                        # Datos del cliente
                        partner_name = record.partner_id.name
                        partner_vat = record.partner_id.vat
                        partner_dpi = record.partner_id.documento_personal_identificacion

                        # Concatenar los campos en una sola cadena
                        description_text = (
                            f"Cliente: {partner_name}\n\n"
                            f"NIT: {partner_vat}\n\n"
                            f"DPI: {partner_dpi}\n\n"
                            f"Producto: {line.product_template_id.name}\n\n"
                            f"Chasis: {line.lot_id}\n\n"
                            f"Vin: {line.x_studio_vin}\n\n"
                            f"Motor: {line.x_studio_no_motor}\n\n"
                            f"Descripcion: {line.name}\n\n"
                            f"Información Adicional: {line.x_studio_inf_adicional}"
                        )

                        # Crear ticket (tarea)
                        self.env['project.task'].sudo().create({
                            'partner_id': record.partner_id.id,
                            'name': line.product_template_id.name,
                            'description': description_text,
                            'project_id': 1,
                            'x_studio_pedido': record.id,
                        })

                        # Marcar como generado
                        record.write({'x_studio_ticket_generado': True})