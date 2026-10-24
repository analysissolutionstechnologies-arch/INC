from odoo import models, fields, api


class ProjectTask(models.Model):
    _inherit = 'project.task'

    # def action_refresh_external_urls(self):
    #     for task in self:
    #         for attachment in task.sale_order_attachment_ids:
    #             attachment._compute_view_external_url()
