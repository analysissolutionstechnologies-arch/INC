# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class POSConfig(models.Model):
	_inherit = 'pos.config' 
	
	enable_lock = fields.Boolean(string='POS Screen Lock Timer')
	lock_timer = fields.Integer(string="Seconds of Time Interval ")

class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	enable_lock = fields.Boolean(related='pos_config_id.enable_lock', readonly=False)
	lock_timer = fields.Integer(related='pos_config_id.lock_timer', readonly=False)