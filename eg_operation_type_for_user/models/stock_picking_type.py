from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    allow_user_ids = fields.Many2many("res.users", string="Allow Users")