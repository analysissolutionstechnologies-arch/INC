# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResCompany(models.Model):
	_inherit = 'res.company'


	allow_warehouse = fields.Boolean(string="Allow Warehouse in Sale Order Line", default=False)


class ResConfigSettings(models.TransientModel): 
	_inherit = 'res.config.settings'

	allow_warehouse = fields.Boolean(string="Allow Warehouse in Sale Order Line", related='company_id.allow_warehouse',readonly=False,)
