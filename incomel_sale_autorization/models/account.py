# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"



    #Verificar Autorizacion NETFINANCE
    sale_order_incomel_id = fields.Many2one('sale.order', string="Sale Order", copy=False)
    char_autorization_netfinance = fields.Char(string="Char Autorizacion NETFINANCE", copy=False,
                                               related='sale_order_incomel_id.char_autorization_netfinance', store=True)
    DpiCliente_autorizado = fields.Char(string="DpiCliente NETFINANCE", copy=False ,
                                        related='sale_order_incomel_id.DpiCliente_autorizado', store=True)
    Factura_monto_autorizado = fields.Char(string="Factura NETFINANCE", copy=False , 
                                           related='sale_order_incomel_id.Factura_monto_autorizado', store=True) 
    
    Pagare_monto_autorizado = fields.Char(string="Pagare NETFINANCE", copy=False ,
                                           related='sale_order_incomel_id.Pagare_monto_autorizado', store=True) 
    
    Agencia_autorizada = fields.Char(string="Agencia NETFINANCE", copy=False , 
                                     related='sale_order_incomel_id.Agencia_autorizada', store=True) 
    
    IdPersona_autorizada = fields.Char(string="IdPersona NETFINANCE", copy=False , 
                                       related='sale_order_incomel_id.IdPersona_autorizada', store=True)
    
    cuota_autorizada = fields.Char(string="Cuota NETFINANCE", copy=False , 
                                   related='sale_order_incomel_id.cuota_autorizada', store=True)
    
    porcentaje_descuento_autorizado = fields.Char(string="PorcentajeDescuento NETFINANCE", copy=False ,
                                                     related='sale_order_incomel_id.porcentaje_descuento_autorizado', store=True)
    
    tipo_cliente_autorizado = fields.Char(string="TipoCliente NETFINANCE", copy=False , 
                                          related='sale_order_incomel_id.tipo_cliente_autorizado', store=True)
    
    monto_plus_autorizado = fields.Char(string="MontoPlus NETFINANCE", copy=False , 
                                         related='sale_order_incomel_id.monto_plus_autorizado', store=True) 
    
    enganche_autorizado = fields.Char(string="Enganche NETFINANCE", copy=False , 
                                      related='sale_order_incomel_id.enganche_autorizado', store=True)
    
    TipoFlujo = fields.Char(string="TipoFlujo", copy=False ,
                            related='sale_order_incomel_id.TipoFlujo', store=True)
    
    Plazo = fields.Char(string="Plazo", copy=False ,
                        related='sale_order_incomel_id.Plazo', store=True)

    nro_items_invoice = fields.Integer(string="Nro. Items Invoice" , compute="compute_nro_items_invoice", copy=False)
    
    
    def button_asignar_sale_order(self):
        for rec in self:
            search_all_invoice_without_saleorder = self.env['account.move'].search([('sale_order_incomel_id', '=', False) ,
                                                                                    ('move_type', '=', 'out_invoice')])
            for invoice in search_all_invoice_without_saleorder:
                if invoice.origin:
                    search_sale = self.env['sale.order'].search([('name', '=', invoice.origin)] , limit=1)
                    if search_sale:
                        invoice.sale_order_incomel_id = invoice.search_sale.id
    

    def button_asignar_sale_from_sale2(self):
        for rec in self:
            search_all_invoice_without_saleorder = self.env['sale.order'].search([('invoice_ids', '!=', False) ,])
            for sale in search_all_invoice_without_saleorder:
                invoice = sale.invoice_ids[0]
                invoice.sale_order_incomel_id = sale.id
    

    def compute_nro_items_invoice(self):
        for rec in self:
            rec.nro_items_invoice = len(rec.invoice_line_ids)



