# -*- coding: utf-8 -*-

from odoo import api, models, fields, _

class PosConfig(models.Model):
    _inherit = 'pos.config'

    pw_change_logo = fields.Boolean('Change Logo')
    pw_pos_logo = fields.Binary(string="POS Logo")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pw_change_logo = fields.Boolean(related='pos_config_id.pw_change_logo', readonly=False)
    pw_pos_logo = fields.Binary(string="POS Logo", related='pos_config_id.pw_pos_logo', readonly=False)
