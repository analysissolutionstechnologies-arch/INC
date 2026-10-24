# -*- coding: utf-8 -*-

from odoo import api, fields, models,tools, _


class PosConfigInherit(models.Model):
	_inherit = 'pos.config'

	order_barcode = fields.Boolean('Order Barcode')
	barcode_selection = fields.Selection([('qrcode', 'QRCode'), ('barcode', 'Barcode')], string="Code")
	invoice_number = fields.Boolean('Invoice Number')
	customer_details = fields.Boolean('Customer Details')
	customer_name = fields.Boolean('Customer Name')
	customer_address = fields.Boolean('Customer Address')
	customer_mobile = fields.Boolean('Customer Mobile')
	customer_phone = fields.Boolean('Customer Phone')
	order_number = fields.Boolean('Order Number')
	customer_email = fields.Boolean('Customer Email')
	customer_vat = fields.Boolean('Customer Vat')

	#campos ventas
	cuota_autorizada = fields.Boolean('Invoice cuota_autorizada')
	plazo = fields.Boolean('Invoice Plazo')
	TipoFlujo = fields.Boolean('Invoice TipoFlujo')

	#campos fel account move
	fel_serie = fields.Char('Invoice fel_serie')
	fel_numero = fields.Char('Invoice fel_numero')
	fel_numero_autorizacion = fields.Char('Invoice fel_numero_autorizacion')



class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	order_barcode = fields.Boolean(related='pos_config_id.order_barcode', readonly=False)
	barcode_selection = fields.Selection(related='pos_config_id.barcode_selection', readonly=False)
	invoice_number = fields.Boolean(related='pos_config_id.invoice_number', readonly=False)
	customer_details = fields.Boolean(related='pos_config_id.customer_details', readonly=False)
	customer_name = fields.Boolean(related='pos_config_id.customer_name', readonly=False)
	customer_address = fields.Boolean(related='pos_config_id.customer_address', readonly=False)
	customer_mobile = fields.Boolean(related='pos_config_id.customer_mobile', readonly=False)
	customer_phone = fields.Boolean(related='pos_config_id.customer_phone', readonly=False)
	order_number = fields.Boolean(related='pos_config_id.order_number', readonly=False)
	customer_email = fields.Boolean(related='pos_config_id.customer_email', readonly=False)
	customer_vat = fields.Boolean(related='pos_config_id.customer_vat', readonly=False)



	#campos ventas
	cuota_autorizada = fields.Boolean('Invoice cuota_autorizada')
	plazo = fields.Boolean('Invoice Plazo')
	TipoFlujo = fields.Boolean('Invoice TipoFlujo')

	#campos fel account move
	fel_serie = fields.Char('Invoice fel_serie')
	fel_numero = fields.Char('Invoice fel_numero')
	fel_numero_autorizacion = fields.Char('Invoice fel_numero_autorizacion')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: