from odoo import models

class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_product_pricelist(self):
        result = super()._loader_params_product_pricelist()
        if 'x_studio_reestriccion_pos' not in result['search_params']['fields']:
            result['search_params']['fields'].append('x_studio_reestriccion_pos')
        return result