# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##########################################################################

from odoo import fields, models, api

class purchase_history(models.Model):
    _name = 'purchase.history'
    _rec_name= 'po_order'
    _order = 'id desc'

    partner_id = fields.Many2one('res.partner',string="Supplier", domain=[('supplier','=',True)])
    order_date = fields.Datetime(string="Date")
    qty = fields.Float(string="Quantity")
    product_id = fields.Many2one('product.template',string='product')
    po_order = fields.Many2one('purchase.order',string='PO Number')
    remark = fields.Char(string='Remark')
    price = fields.Float(string='Price')
    purchase_line_id = fields.Many2one('purchase.order.line', string='Purchase Line')
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: