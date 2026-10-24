from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # def action_refresh_external_urls(self):
    #     for order in self:
    #         for attachment in order.x_studio_adjuntos:
    #             attachment._compute_view_external_url()
