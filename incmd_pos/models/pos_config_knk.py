# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).


from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    hide_refund_button = fields.Boolean(string='Hide Refund Button')
