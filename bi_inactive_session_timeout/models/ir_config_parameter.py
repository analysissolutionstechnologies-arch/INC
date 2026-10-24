# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import json
import werkzeug
from lxml import etree
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import ValidationError
from odoo.http import request

class IrConfigParameter(models.Model):
    _inherit = "ir.config_parameter"



    @api.model
    @tools.ormcache("self.env.cr.dbname")
    def _session_timeout_delay(self):
        value=int(self.env["ir.config_parameter"].sudo().get_param('session_timeout_time',5000,))
        value=value*60
        return value
    
