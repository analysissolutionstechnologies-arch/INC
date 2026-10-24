from odoo import api, fields, models, _


class PosOrderType(models.Model):
	_name = 'pos.order.type'
	_description = "POS Order Types"

	name = fields.Char('Name', required=True)


class PosConfig(models.Model):
	_inherit = 'pos.config'

	enable_order_type = fields.Boolean('Enable Type of POS order')
	order_type_ids = fields.Many2many('pos.order.type', string='Type of POS order')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_order_type = fields.Boolean(related='pos_config_id.enable_order_type',readonly=False)
    order_type_ids = fields.Many2many(related='pos_config_id.order_type_ids',readonly=False)


class pos_order(models.Model):
	_inherit = 'pos.order'

	order_type_id = fields.Many2one('pos.order.type',string='Tipo de Pedido ')

	def _order_fields(self, ui_order):
		res = super(pos_order, self)._order_fields(ui_order)
		res.update({
			'order_type_id': ui_order.get('order_type_id'),
			})
		return res


class POSSession(models.Model):
	_inherit = 'pos.session'


	def _pos_ui_models_to_load(self):
		result = super()._pos_ui_models_to_load()
		result.extend(['pos.order.type'])
		return result

	def _loader_params_pos_order_type(self):
		return {
			'search_params': {
				'domain': [('id', 'in', self.config_id.order_type_ids.ids)], 
				'fields': ['name','id'],
			}
		}

	def _get_pos_ui_pos_order_type(self, params):
		return self.env['pos.order.type'].search_read(**params['search_params'])
