# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools,_
from odoo.tools import float_is_zero, float_compare,format_datetime
from collections import defaultdict
import json

class ProductTemplate(models.Model):
	_inherit = "product.template"

	warehouse_quantity = fields.Char(compute='_get_quantity_warehouse_location', string='Quantity per warehouse')
	warehouse_id = fields.Many2one(compute='_get_quantity_warehouse_forcast_location', string='Warehouse Name')


	def _get_quantity_warehouse_location(self):
		for record in self:
			text = ''
			product_id = self.env['product.product'].sudo().search([('product_tmpl_id', '=', record.id)])
			if product_id:
				quant_ids = self.env['stock.quant'].sudo().search([('product_id','=',product_id[0].id),('location_id.usage','=','internal')])
				res = {}
				for quant in quant_ids:
					if quant.location_id:
						if quant.location_id not in res:
							res.update({quant.location_id:0})
						res[quant.location_id] += quant.quantity

				res1 = {}
				for location in res:
					warehouse = False
					location1 = location
					while (not warehouse and location1):
						warehouse_id = self.env['stock.warehouse'].sudo().search([('lot_stock_id','=',location1.id)])
						if len(warehouse_id) > 0:
							warehouse = True
						else:
							warehouse = False
						location1 = location1.location_id
					if warehouse_id:
						if warehouse_id.name not in res1:
							res1.update({warehouse_id.name:0})
						res1[warehouse_id.name] += res[location]

				for item in res1:
					if res1[item] != 0:
						text = text + item + ': ' + str(res1[item])
				record.warehouse_quantity = text


	def _get_quantity_warehouse_forcast_location(self):
		for record in self:
			text = ''
			product_id = self.env['product.product'].sudo().search([('product_tmpl_id', '=', record.id)])
			if product_id:
				quant_ids = self.env['stock.quant'].sudo().search([('product_id','=',product_id[0].id),('location_id.usage','=','internal')])
				res = {}
				for quant in quant_ids:
					if quant.location_id:
						if quant.location_id not in res:
							res.update({quant.location_id:0})
						res[quant.location_id] += quant.virtual_available

				res1 = {}
				for location in res:
					warehouse = False
					location1 = location
					while (not warehouse and location1):
						warehouse_id = self.env['stock.warehouse'].sudo().search([('lot_stock_id','=',location1.id)])
						if len(warehouse_id) > 0:
							warehouse = True
						else:
							warehouse = False
						location1 = location1.location_id
					if warehouse_id:
						if warehouse_id.name not in res1:
							res1.update({warehouse_id.name:0})
						res1[warehouse_id.name] += res[location]

				for item in res1:
					if res1[item] != 0:
						text = text + item + ': ' + str(res1[item])
				record.warehouse_quantity = text









class PosOrderLinePicking(models.Model):
	_inherit = 'pos.order.line'

	stock_location_name = fields.Char('Warehouse')


class PosOrderPicking(models.Model):
	_inherit = 'pos.order'

	stock_location_name = fields.Char('Warehouse')


	def _create_order_picking(self):
		self.ensure_one()
		if self.shipping_date:
			self.sudo().lines._launch_stock_rule_from_pos_order_lines()
		else:
			if self._should_create_picking_real_time():
				picking_type = self.config_id.picking_type_id
				if self.partner_id.property_stock_customer:
					destination_id = self.partner_id.property_stock_customer.id
				elif not picking_type or not picking_type.default_location_dest_id:
					destination_id = self.env['stock.warehouse']._get_partner_locations()[0].id
				else:
					destination_id = picking_type.default_location_dest_id.id

				different = self.lines.filtered(lambda l: l.stock_location_name)

				if different:
					for line in different:
						picking_type = self.env['stock.picking.type'].search(
							[('warehouse_id.name', '=', line.stock_location_name), ('code', '=', 'outgoing'),
							 ('sequence_code', '=', 'POS')])

						diff_pick = self.env['stock.picking'].with_context(diff_loc=line.stock_location_name)._create_picking_from_pos_order_lines(destination_id, line, picking_type, self.partner_id)
						diff_pick.write({'pos_session_id': self.session_id.id, 'pos_order_id': self.id,'pos_order_id': self.id, 'origin': self.name})

				else:
					pickings = self.env['stock.picking']._create_picking_from_pos_order_lines(destination_id, self.lines, picking_type, self.partner_id)
					pickings.write({'pos_session_id': self.session_id.id, 'pos_order_id': self.id, 'origin': self.name})



class Product(models.Model):
	_inherit = 'product.product'


	quant_ids = fields.One2many("stock.quant", "product_id", string="Quants",
								domain=[('location_id.usage', '=', 'internal')])

	quant_text = fields.Text('Quant Qty', compute='_compute_avail_locations', store=True)

	@api.depends('stock_quant_ids', 'stock_quant_ids.product_id', 'stock_quant_ids.location_id',
				 'stock_quant_ids.quantity')
	def _compute_avail_locations(self):
		notifications = []
		for rec in self:
			final_data = {}
			rec.quant_text = json.dumps(final_data)
			if rec.type == 'product':
				quants = self.env['stock.quant'].sudo().search(
					[('product_id', 'in', rec.ids), ('location_id.usage', '=', 'internal')])
				outgoing = self.env['stock.move'].sudo().search(
					[('product_id', '=', rec.id), ('state', 'not in', ['done','cancel']),
					 ('location_id.usage', '=', 'internal'),
					 ('picking_id.picking_type_code', 'in', ['outgoing'])])
				incoming = self.env['stock.move'].sudo().search(
					[('product_id', '=', rec.id), ('state', 'not in', ['done','cancel']),
					 ('location_dest_id.usage', '=', 'internal'),
					 ('picking_id.picking_type_code', 'in', ['incoming'])])
				for quant in quants:
					loc = quant.location_id.id
					if loc in final_data:
						last_qty = final_data[loc][0]
						final_data[loc][0] = last_qty + quant.quantity
					else:
						final_data[loc] = [quant.quantity, 0, 0]

				for out in outgoing:
					loc = out.location_id.id
					if loc in final_data:
						last_qty = final_data[loc][1]
						final_data[loc][1] = last_qty + out.product_qty
					else:
						final_data[loc] = [0, out.product_qty, 0]

				for inc in incoming:
					loc = inc.location_dest_id.id
					if loc in final_data:
						last_qty = final_data[loc][2]
						final_data[loc][2] = last_qty + inc.product_qty
					else:
						final_data[loc] = [0, 0, inc.product_qty]

				rec.quant_text = json.dumps(final_data)
		return True


	def _product_domain(self, product_template_ids, product_variant_ids):
		if product_template_ids:
			return [('product_tmpl_id', 'in', product_template_ids)]
		return [('product_id', 'in', product_variant_ids)]

	def _move_domain(self, product_template_ids, product_variant_ids, wh_location_ids):
		move_domain = self._product_domain(product_template_ids, product_variant_ids)
		move_domain += [('product_uom_qty', '!=', 0)]
		out_domain = move_domain + [
			'&',
			('location_id', 'in', wh_location_ids),
			('location_dest_id', 'not in', wh_location_ids),
		]
		in_domain = move_domain + [
			'&',
			('location_id', 'not in', wh_location_ids),
			('location_dest_id', 'in', wh_location_ids),
		]
		return in_domain, out_domain

	def _move_draft_domain(self, product_template_ids, product_variant_ids, wh_location_ids):
		in_domain, out_domain = self._move_domain(product_template_ids, product_variant_ids, wh_location_ids)
		in_domain += [('state', '=', 'draft')]
		out_domain += [('state', '=', 'draft')]
		return in_domain, out_domain

	def _move_confirmed_domain(self, product_template_ids, product_variant_ids, wh_location_ids):
		in_domain, out_domain = self._move_domain(product_template_ids, product_variant_ids, wh_location_ids)
		out_domain += [('state', 'not in', ['draft', 'cancel', 'done'])]
		in_domain += [('state', 'not in', ['draft', 'cancel', 'done'])]
		return in_domain, out_domain

	def _compute_draft_quantity_count(self, product_template_ids, product_variant_ids, wh_location_ids):
		in_domain, out_domain = self._move_draft_domain(product_template_ids, product_variant_ids, wh_location_ids)
		incoming_moves = self.env['stock.move'].read_group(in_domain, ['product_qty:sum'], 'product_id')
		outgoing_moves = self.env['stock.move'].read_group(out_domain, ['product_qty:sum'], 'product_id')
		in_sum = sum(move['product_qty'] for move in incoming_moves)
		out_sum = sum(move['product_qty'] for move in outgoing_moves)
		return {
			'draft_picking_qty': {
				'in': in_sum,
				'out': out_sum
			},
			'qty': {
				'in': in_sum,
				'out': out_sum
			}
		}

	@api.model
	def _get_report_values(self, docids, data=None):
		return {
			'data': data,
			'doc_ids': docids,
			'doc_model': 'product.product',
			'docs': self._get_report_data(product_variant_ids=docids),
		}

	def _get_report_data(self, product_template_ids=False, product_variant_ids=False):
		assert product_template_ids or product_variant_ids
		res = {}

		# Get the warehouse we're working on as well as its locations.
		if self.env.context.get('warehouse'):
			warehouse = self.env['stock.warehouse'].sudo().browse(self.env.context['warehouse'])
		else:
			warehouse = self.env['stock.warehouse'].sudo().search([
				('company_id', '=', self.env.company.id)
			], limit=1)
			self.env.context = dict(self.env.context, warehouse=warehouse.id)
		wh_location_ids = [loc['id'] for loc in self.env['stock.location'].search_read(
			[('id', 'child_of', warehouse.view_location_id.id), ('usage', '=', 'internal')],
			['id'],
		)]
		res['active_warehouse'] = warehouse.display_name

		# Get the products we're working, fill the rendering context with some of their attributes.
	   
		if product_template_ids:
			product_templates = self.env['product.template'].browse(product_template_ids)
			res['product_templates'] = product_templates
			res['product_variants'] = product_templates.product_variant_ids
			res['multiple_product'] = len(product_templates.product_variant_ids) > 1
			res['uom'] = product_templates[:1].uom_id.display_name
			product_ids = product_templates.product_variant_ids.ids
			quants = self.env['stock.quant'].search([
				('location_id', 'in', wh_location_ids),
				('product_id', 'in', product_ids)
			])
			res['quantity_on_hand'] = sum(quants.mapped('quantity'))
			res['virtual_available'] = sum(product_templates.mapped('virtual_available'))
		
		if product_variant_ids:
			product_variants = self.env['product.product'].browse(product_variant_ids)
			res['product_templates'] = False
			res['product_variants'] = product_variants
			res['multiple_product'] = len(product_variants) > 1
			res['uom'] = product_variants[:1].uom_id.display_name
			product_ids = product_variants.ids
			quants = self.env['stock.quant'].search([
				('location_id', 'in', wh_location_ids),
				('product_id', 'in', product_ids)
			])
			res['quantity_on_hand'] = sum(quants.mapped('quantity'))
			res['virtual_available'] = sum(product_variants.mapped('virtual_available'))
		res.update(self._compute_draft_quantity_count(product_template_ids, product_variant_ids, wh_location_ids))

		res['lines'] = self._get_report_lines(product_template_ids, product_variant_ids, wh_location_ids)
		return res

	def _prepare_report_line(self, quantity, move_out=None, move_in=None, replenishment_filled=True, product=False, reservation=False):
		timezone = self._context.get('tz')
		product = product or (move_out.product_id if move_out else move_in.product_id)
		is_late = move_out.date < move_in.date if (move_out and move_in) else False
		return {
			'document_in': move_in._get_source_document() if move_in else False,
			'document_out': move_out._get_source_document() if move_out else False,
			'product': {
				'id': product.id,
				'display_name': product.display_name
			},
			'replenishment_filled': replenishment_filled,
			'uom_id': product.uom_id,
			'receipt_date': format_datetime(self.env, move_in.date, timezone, 'medium') if move_in else False,
			'delivery_date': format_datetime(self.env, move_out.date, timezone, 'medium') if move_out else False,
			'is_late': is_late,
			'quantity': quantity,
			'move_out': move_out,
			'move_in': move_in,
			'reservation': reservation,
		}

	def _get_report_lines(self, product_template_ids, product_variant_ids, wh_location_ids):
		in_domain, out_domain = self._move_confirmed_domain(
			product_template_ids, product_variant_ids, wh_location_ids
		)
		outs = self.env['stock.move'].search(out_domain, order='priority desc, date, id')
		outs_per_product = defaultdict(lambda: [])
		for out in outs:
			outs_per_product[out.product_id.id].append(out)
		ins = self.env['stock.move'].search(in_domain, order='priority desc, date, id')
		ins_per_product = defaultdict(lambda: [])
		for in_ in ins:
			ins_per_product[in_.product_id.id].append([in_.product_qty, in_])
		currents = {c['id']: c['qty_available'] for c in outs.product_id.with_context(location=wh_location_ids).read(['qty_available'])}

		lines = []
		for product in (ins | outs).product_id:
			for out in outs_per_product[product.id]:
				if out.state not in ('partially_available', 'assigned'):
					continue
				current = currents[out.product_id.id]
				reserved = out.product_uom._compute_quantity(out.availability, product.uom_id)
				currents[product.id] -= reserved
				lines.append(self._prepare_report_line(reserved, move_out=out, reservation=True))

			for out in outs_per_product[product.id]:
				# Reconcile with the current stock.
				current = currents[out.product_id.id]
				reserved = 0.0
				if out.state in ('partially_available', 'assigned'):
					reserved = out.product_uom._compute_quantity(out.availability, product.uom_id)
				demand = out.product_qty - reserved
				taken_from_stock = min(demand, current)
				if not float_is_zero(taken_from_stock, precision_rounding=product.uom_id.rounding):
					currents[product.id] -= taken_from_stock
					demand -= taken_from_stock
					lines.append(self._prepare_report_line(taken_from_stock, move_out=out))
				# Reconcile with the ins.
				if not float_is_zero(demand, precision_rounding=product.uom_id.rounding):
					index_to_remove = []
					for index, in_ in enumerate(ins_per_product[out.product_id.id]):
						if float_is_zero(in_[0], precision_rounding=product.uom_id.rounding):
							continue
						taken_from_in = min(demand, in_[0])
						demand -= taken_from_in
						lines.append(self._prepare_report_line(taken_from_in, move_in=in_[1], move_out=out))
						ins_per_product[out.product_id.id][index][0] -= taken_from_in
						if ins_per_product[out.product_id.id][index][0] <= 0:
							index_to_remove.append(index)
						if float_is_zero(demand, precision_rounding=product.uom_id.rounding):
							break
					for index in index_to_remove[::-1]:
						ins_per_product[out.product_id.id].pop(index)
				# Not reconciled.
				if not float_is_zero(demand, precision_rounding=product.uom_id.rounding):
					lines.append(self._prepare_report_line(demand, move_out=out, replenishment_filled=False))
			# Unused remaining stock.
			free_stock = currents.get(product.id, 0)
			if not float_is_zero(free_stock, precision_rounding=product.uom_id.rounding):
				lines.append(self._prepare_report_line(free_stock, product=product))
			# In moves not used.
			for in_ in ins_per_product[product.id]:
				if float_is_zero(in_[0], precision_rounding=product.uom_id.rounding):
					continue
				lines.append(self._prepare_report_line(in_[0], move_in=in_[1]))
		return lines

	@api.model
	def get_filter_state(self):
		res = {}
		res['warehouses'] = self.env['stock.warehouse'].sudo().search_read(fields=['id', 'name', 'code'])
		res['active_warehouse'] = self.env.context.get('warehouse', False)
		if not res['active_warehouse']:
			res['active_warehouse'] = self.env.context.get('allowed_company_ids')[0]
		return res
