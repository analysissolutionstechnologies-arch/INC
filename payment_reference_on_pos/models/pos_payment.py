from odoo import fields, models, _


class PosPayment(models.Model):
    """To add a field in pos payment related to pos session"""
    _inherit = 'pos.payment'
    
    payment_reference = fields.Char(string='Payment Reference',readonly=True, copy=False, help="The document that was utilized to issue this payment. For example, check number, file name, and so on.")
    bank_id = fields.Many2one('res.bank', 'Banco')
    number_quote = fields.Selection([
        ('corriente_1', 'Corriente'),
        ('corriente_3', 'Plazo 3 Cuotas'),
        ('corriente_6', 'Plazo 6 Cuotas'),
        ('corriente_10', 'Plazo 10 Cuotas'),
        ('corriente_12', 'Plazo 12 Cuotas'),
        ('corriente_15', 'Plazo 15 Cuotas'),
        ('corriente_18', 'Plazo 18 Cuotas'),
        ('corriente_24', 'Plazo 24 Cuotas'),
        ('corriente_36', 'Plazo 36 Cuotas'),
        ('corriente_48', 'Plazo 48 Cuotas')
    ], string='Cuotas')
    card_termination = fields.Char('Terminacion tarjeta')
    auth_number = fields.Char('NO. autorizacion')
    comment = fields.Char('Observaciones')