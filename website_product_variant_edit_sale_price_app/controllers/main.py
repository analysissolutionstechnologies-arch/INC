# -*- coding: utf-8 -*-

import json
import logging
from odoo import fields, http, tools, _
from odoo.http import request
from odoo.addons.website.controllers.main import Website

_logger = logging.getLogger(__name__)
from odoo.addons.website_sale.controllers.main import WebsiteSale

class WebsiteSales(WebsiteSale):
	@http.route(['/product_configurator/get_combination_info_website'], type='json', auth="public", methods=['POST'], website=True)
	def get_combination_info_website(self, product_template_id, product_id, combination, add_qty, **kw):
		kw.pop('pricelist_id')
		combination = self.get_combination_info(product_template_id, product_id, combination, add_qty, request.website.get_current_pricelist(), **kw)
		product = request.env['product.product'].browse(combination['product_id'])
		if product.new_list_price:
			combination.update({
				'list_price' : product.new_list_price, 'price' : product.new_list_price,
				})
		else:
			combination.update({
				'list_price' : product.lst_price, 'price' : product.lst_price,
				})
		if request.website.google_analytics_key:
			combination['product_tracking_info'] = request.env['product.template'].get_google_analytics_data(combination)
		if product.new_list_price:
			carousel_view = request.env['ir.ui.view']._render_template('website_sale.shop_product_carousel', values={
				'list_price' : product.new_list_price, 'price' : product.new_list_price,
				'product': request.env['product.template'].browse(combination['product_template_id']),
				'product_variant': request.env['product.product'].browse(combination['product_id']),
			})
		else:
			carousel_view = request.env['ir.ui.view']._render_template('website_sale.shop_product_carousel', values={
				'product': request.env['product.template'].browse(combination['product_template_id']),
				'product_variant': request.env['product.product'].browse(combination['product_id']),
			})

		combination['carousel'] = carousel_view
		return combination


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: