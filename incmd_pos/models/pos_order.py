from odoo import models

class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _prepare_invoice_vals(self):
        invoice_vals = super()._prepare_invoice_vals()
        # Usar la lista de precios del cliente si existe, si no, la del pedido POS
        partner = self.partner_id
        pricelist_id = partner.property_product_pricelist.id if partner and partner.property_product_pricelist else self.pricelist_id.id
        invoice_vals['x_studio_lista_de_precio'] = pricelist_id
        invoice_vals['x_studio_lista_de_precio_1'] = pricelist_id
        return invoice_vals

    def action_pos_order_invoice(self):
        res = super().action_pos_order_invoice()
        for order in self:
            if order.account_move:
                partner = order.partner_id
                pricelist_id = partner.property_product_pricelist.id if partner and partner.property_product_pricelist else order.pricelist_id.id
                order.account_move.write({
                    'x_studio_lista_de_precio': pricelist_id,
                    'x_studio_lista_de_precio_1': pricelist_id,
                })
        return res