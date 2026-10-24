from odoo import http
from odoo.http import request

class PricelistPaymentMethodController(http.Controller):
    @http.route('/pos/pricelist_payment_methods', type='json', auth='user')
    def get_pricelist_payment_methods(self):
        records = request.env['x_product.pricelist.payment.method'].search([('x_status_registry', '=', True)])
        return [
            {
                'pricelist_id': rec.x_product_pricelist.id,
                'payment_method_ids': [pm.id for pm in rec.x_payment_method],
            }
            for rec in records
        ]