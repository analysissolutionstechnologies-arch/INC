from odoo import models, fields, api, _
from odoo.tools import formatLang, float_is_zero
from odoo.exceptions import ValidationError


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    bank_ids = fields.Many2many('res.bank', string='Bancos')
    # bank_id = fields.Many2one('res.partner.bank', 'Banco')