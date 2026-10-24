# -*- coding: utf-8 -*-

from odoo import fields, models

class ResUsers(models.Model):
    _inherit = 'res.users'

    last_signin_at = fields.Datetime(string='Last Signin At')