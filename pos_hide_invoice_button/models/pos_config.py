from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    hide_invoice_button = fields.Boolean(default=False)
    
    
    
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    hide_invoice_button = fields.Boolean(related='pos_config_id.hide_invoice_button',readonly=False)    
