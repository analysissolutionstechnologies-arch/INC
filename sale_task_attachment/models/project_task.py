from odoo import models, fields, api

class ProjectTask(models.Model):
    _inherit = 'project.task'

    sale_order_attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Sale Order Attachments',
        compute='_compute_sale_order_attachment_ids'
    )

    @api.depends('x_studio_pedido')
    def _compute_sale_order_attachment_ids(self):
        for task in self:
            if task.x_studio_pedido:
                # Simplemente asigna los adjuntos existentes sin modificarlos
                attachments = task.x_studio_pedido.x_studio_adjuntos
                task.sale_order_attachment_ids = attachments
            else:
                task.sale_order_attachment_ids = self.env['ir.attachment']

