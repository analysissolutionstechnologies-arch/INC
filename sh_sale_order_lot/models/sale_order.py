# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import api, fields, models, _
import warnings
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    lot_id = fields.Many2one(
        'stock.lot', 'Lot', copy=False)

    available_lot_ids = fields.Many2many(
        'stock.lot',
        string='Available Lots',
        compute='_compute_available_lot_ids'
    )

    @api.onchange('product_id', 'warehouses_id')
    def _onchange_product_id_set_lot_domain(self):
        available_lot_ids = []
        if self.warehouses_id  and self.product_id:
            location = self.warehouses_id.lot_stock_id
            quants = self.env['stock.quant'].read_group([
                ('product_id', '=', self.product_id.id),
                ('location_id', 'child_of', location.id),
                ('quantity', '>', 0),
                ('lot_id', '!=', False),
            ], ['lot_id'], 'lot_id')
            available_lot_ids = [quant['lot_id'][0] for quant in quants]
        self.lot_id = False
        return {
            'domain': {'lot_id': [('id', 'in', available_lot_ids)]}
        }



    @api.depends('product_id', 'warehouses_id')
    def _compute_available_lot_ids(self):
        available_lot_ids = []
        for rec in self:
            if rec.warehouses_id and rec.product_id:
                # Obtener todas las ubicaciones de stock del almacén seleccionado
                warehouse_locations = self.env['stock.location'].search([
                    ('warehouse_id', 'in', rec.warehouses_id.ids),
                    ('usage', '=', 'internal')  # Considerar solo ubicaciones internas (de stock)
                ])
                location_ids = warehouse_locations.ids
                _logger.info("location_ids: %s", location_ids)
                _logger.info("almacen: %s", rec.warehouse_id.name)
                _logger.info("almacenes: %s", rec.warehouses_id.name)
                
                for location in warehouse_locations:
                    _logger.info("location: %s", location.name)
                domain = [('location_id', 'in', location_ids),
                        ('product_id', '=', rec.product_id.id),
                        ('quantity', '>', 0),
                        ('lot_id', '!=', False),
                    ]
                _logger.info("domain: %s", domain)

                quants = self.env['stock.quant'].read_group(domain, ['lot_id'], 'lot_id')

                _logger.info("quants: %s", quants)

                available_lot_ids = [quant['lot_id'][0] for quant in quants]
                _logger.info("available_lot_ids: %s", available_lot_ids)
                    
            rec.available_lot_ids = available_lot_ids





class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def get_move_from_line(self, line):
        move = self.env['stock.move']
        lot_count = 0
        for pp in line.order_id.picking_ids:
            for mm in pp.move_ids:
                lot_ids = [mv_line.lot_id.id for mv_line in mm.move_line_ids]
                if line.lot_id.id:
                    for lot_line in mm.move_line_ids:
                        if lot_line.product_id == line.product_id:
                            lot_line.lot_id = line.lot_id.id
                if line.lot_id.id in lot_ids:
                    move = mm
                    lot_count += 1
                    if lot_count != 1:
                        raise warnings.warn(_('Can\'t retrieve lot on stock'))
        return move

    @api.model
    def _check_move_state(self, line):
        if line.lot_id:
            move = self.get_move_from_line(line)
            if move and move.state == 'confirmed':
                move.action_assign()
                move.refresh()
            if move and move.state != 'assigned':
                raise warnings.warn(_('Can\'t reserve products for lot %s') %
                              line.lot_id.name)
        return True

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for line in self.order_line:
            self._check_move_state(line)
        return res
