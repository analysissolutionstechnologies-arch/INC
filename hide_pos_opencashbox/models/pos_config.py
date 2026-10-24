# -*- coding: utf-8 -*-

from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    hide_pos_opencashbox = fields.Boolean(
        string="Hide Opening Cash Control",
        default=False
    )

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    hide_pos_opencashbox = fields.Boolean(related='pos_config_id.hide_pos_opencashbox',readonly=False)