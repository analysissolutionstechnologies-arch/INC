# # -*- coding: utf-8 -*-
# # Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

# from odoo import models, fields, api, _

# class SaleOrderLineInherit(models.Model):
#     _inherit = 'sale.order.line'

#     warehouses_id = fields.Many2one('stock.warehouse',string="warehouse")
#     is_warehouse = fields.Boolean()

#     @api.onchange('product_id')
#     def set_required_warehouse(self):
#         company = self.env.company
#         self.is_warehouse = company.allow_warehouse
#         if self.product_id:
#             self.warehouses_id = self.product_id.sale_warehouse_id.id



#     def _prepare_procurement_values(self,group_id):
#         res = super(SaleOrderLineInherit, self)._prepare_procurement_values(group_id=group_id)
        
#         res_config= self.env.company
#         if res_config.allow_warehouse:
#             res.update({
#                 'warehouse_id':self.warehouses_id,
#                 })
            
#         return res

# from odoo import models, fields, api
#
# class SaleOrderLineInherit(models.Model):
#     _inherit = 'sale.order.line'
#
#     warehouses_id = fields.Many2one('stock.warehouse', string="Warehouse")
#     is_warehouse = fields.Boolean()
#     product_available_qty = fields.Float(string="Available Quantity", compute="_compute_product_available_qty")
#
#     @api.onchange('product_id')
#     def set_required_warehouse(self):
#         company = self.env.company
#         self.is_warehouse = company.allow_warehouse
#         if self.product_id:
#             self.warehouses_id = self.product_id.sale_warehouse_id.id
#
#     @api.depends('product_id', 'warehouses_id')
#     def _compute_product_available_qty(self):
#         for line in self:
#             if line.product_id and line.warehouses_id:
#                 # Obtener la cantidad disponible del producto en el almacén seleccionado
#                 stock_quant = self.env['stock.quant'].search([
#                     ('product_id', '=', line.product_id.id),
#                     ('location_id', '=', line.warehouses_id.lot_stock_id.id)
#                 ], limit=1)
#                 line.product_available_qty = stock_quant.quantity if stock_quant else 0.0
#             else:
#                 line.product_available_qty = 0.0
#
#     def _prepare_procurement_values(self, group_id):
#         res = super(SaleOrderLineInherit, self)._prepare_procurement_values(group_id=group_id)
#         res_config = self.env.company
#         if res_config.allow_warehouse:
#             res.update({
#                 'warehouse_id': self.warehouses_id,
#             })
#         return res

from odoo import models, fields, api

class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    warehouses_id = fields.Many2one('stock.warehouse', string="Warehouse")
    is_warehouse = fields.Boolean()
    product_available_qty = fields.Float(
        string="Available Quantity",
        compute="_compute_product_available_qty",
        store=False
    )

    @api.onchange('product_id')
    def set_required_warehouse(self):
        company = self.env.company
        self.is_warehouse = company.allow_warehouse
        if self.product_id:
            self.warehouses_id = self.product_id.sale_warehouse_id.id

    @api.depends('product_id', 'warehouses_id', 'product_uom_qty')
    def _compute_product_available_qty(self):
        for line in self:
            if line.product_id and line.warehouses_id:
                product = line.product_id.with_context(warehouse=line.warehouses_id.id)
                line.product_available_qty = product.free_qty
            else:
                line.product_available_qty = 0.0

    def _prepare_procurement_values(self, group_id):
        res = super(SaleOrderLineInherit, self)._prepare_procurement_values(group_id=group_id)
        res_config = self.env.company
        if res_config.allow_warehouse:
            res.update({
                'warehouse_id': self.warehouses_id,
            })
        return res

