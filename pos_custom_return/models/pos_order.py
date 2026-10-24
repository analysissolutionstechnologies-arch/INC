# import logging
# from odoo import models, fields, api
# from odoo.exceptions import ValidationError
#
# _logger = logging.getLogger(__name__)
#
#
# class PosMakePayment(models.TransientModel):
#     _inherit = 'pos.make.payment'
#
#     def check(self):
#         """
#         Sobrescribe el método check() de pos.make.payment para generar los movimientos de stock
#         después de que el pago de la devolución sea confirmado.
#         """
#         _logger.info("===== EJECUTANDO MÉTODO pos.make.payment.check() =====")
#
#         # 🔥 PASAR CONTEXTO PARA EVITAR TRANSFERENCIAS 🔥
#         self = self.with_context(skip_transfer=True)
#
#         res = super(PosMakePayment, self).check()  # Procesar el pago antes de continuar
#
#         StockPicking = self.env['stock.picking']
#         StockMove = self.env['stock.move']
#         StockLocation = self.env['stock.location']
#
#         # Obtener la orden activa desde el contexto
#         active_id = self.env.context.get('active_id')
#         if not active_id:
#             _logger.warning("❌ No se encontró una orden activa en el contexto.")
#             return res
#
#         order = self.env['pos.order'].browse(active_id)
#         _logger.info(f"🛒 Procesando orden: {order.name} (ID: {order.id}), Estado: {order.state}")
#
#         # 🔥 SOLO EJECUTAR SI ES UNA DEVOLUCIÓN 🔥
#         if not order.refunded_order_ids:
#             _logger.warning(f"❌ La orden {order.name} no es una devolución. No se ejecuta el proceso.")
#             return res
#
#         # Si existe el campo `is_refund`, verificarlo también
#         if hasattr(order, 'is_refund') and not order.is_refund:
#             _logger.warning(f"❌ La orden {order.name} no está marcada como reembolso. No se ejecuta el proceso.")
#             return res
#
#         # 🔥 OBTENER ORDEN ORIGINAL DESDE EL BOTÓN "ÓRDENES REEMBOLSADAS" 🔥
#         original_order = order.refunded_order_ids[:1]
#         if not original_order:
#             _logger.warning(f"⚠ No se pudo obtener la orden original desde el botón inteligente.")
#             return res
#
#         # 🔥 LOG DE LA ORDEN ORIGINAL ENCONTRADA 🔥
#         _logger.info(f"📌 Orden Original Encontrada: {original_order.name} (ID: {original_order.id})")
#
#         original_picking = original_order.picking_ids.filtered(lambda p: p.state == 'done')
#         if not original_picking:
#             _logger.warning(f"⚠ La orden original {original_order.name} NO tiene recolecciones asociadas, SE OMITE.")
#             return res
#
#         # 🔥 MAPEAR RECOLECCIONES ORIGINALES ANTES DE LA EJECUCIÓN 🔥
#         original_picking_ids = original_picking.ids
#         _logger.info(f"📦 Recolecciones originales antes de la ejecución: {original_picking_ids}")
#
#         # 🔥 CREAR PICKING DE DEVOLUCIÓN 🔥
#         customer_location = StockLocation.search([('usage', '=', 'customer')], limit=1)
#         if not customer_location:
#             _logger.error("❌ ERROR: No se encontró la ubicación de clientes.")
#             raise ValidationError("No se encontró la ubicación de clientes.")
#
#         return_picking = StockPicking.create({
#             'partner_id': order.partner_id.id,
#             'picking_type_id': original_picking[
#                 0].picking_type_id.return_picking_type_id.id if original_picking else False,
#             'location_id': customer_location.id,
#             'location_dest_id': original_picking[
#                 0].picking_type_id.default_location_dest_id.id if original_picking else False,
#             'origin': f"RET/{order.name}",
#         })
#
#         _logger.info(f"✅ Albarán de devolución creado: {return_picking.name} (ID: {return_picking.id})")
#
#         new_moves = self.env['stock.move']
#         for line in order.lines:
#             if line.product_id.type in ['product', 'consu']:
#                 move = StockMove.create({
#                     'name': f"Return {line.product_id.name}",
#                     'product_id': line.product_id.id,
#                     'product_uom_qty': abs(line.qty),
#                     'product_uom': line.product_id.uom_id.id,
#                     'picking_id': return_picking.id,
#                     'location_id': customer_location.id,
#                     'location_dest_id': return_picking.location_dest_id.id,
#                     'origin': f"RET/{order.name}",
#                 })
#                 _logger.info(f"✅ Movimiento de stock creado: {move.name} (ID: {move.id})")
#                 new_moves |= move
#
#         return_picking.action_confirm()
#         return_picking.action_assign()
#         return_picking.button_validate()
#
#         _logger.info(f"✅ Picking validado: {return_picking.name} (ID: {return_picking.id})")
#
#         order.write({'picking_ids': [(4, return_picking.id)]})
#         _logger.info(f"✅ Orden {order.name} (ID: {order.id}) actualizada con picking {return_picking.id}")
#
#         # 🔥 MAPEAR RECOLECCIONES DESPUÉS DE LA EJECUCIÓN 🔥
#         all_pickings_after = original_order.picking_ids.ids
#         new_picking_ids = list(set(all_pickings_after) - set(original_picking_ids))
#         _logger.info(f"🚨 Recolecciones adicionales detectadas: {new_picking_ids}")
#
#         # 🔥 ELIMINAR RECOLECCIONES NUEVAS 🔥
#         if new_picking_ids:
#             pickings_to_delete = self.env['stock.picking'].browse(new_picking_ids).filtered(
#                 lambda p: p.state in ['waiting', 'confirmed'])
#             if pickings_to_delete:
#                 _logger.info(f"🗑 Eliminando {len(pickings_to_delete)} recolecciones creadas en la orden original.")
#                 pickings_to_delete.unlink()
#             else:
#                 _logger.info("✅ No se encontraron recolecciones en estado 'waiting' o 'confirmed' para eliminar.")
#
#         _logger.info("===== FIN DE MÉTODO pos.make.payment.check() =====")
#         return res

# import logging
# from odoo import models, fields, api
# from odoo.exceptions import ValidationError
#
# _logger = logging.getLogger(__name__)
#
#
# class PosMakePayment(models.TransientModel):
#     _inherit = 'pos.make.payment'
#
#     def check(self):
#         """
#         Sobrescribe el método check() de pos.make.payment para generar los movimientos de stock
#         después de que el pago de la devolución sea confirmado.
#         """
#         _logger.info("===== EJECUTANDO MÉTODO pos.make.payment.check() =====")
#
#         # 🔥 PASAR CONTEXTO PARA EVITAR TRANSFERENCIAS 🔥
#         self = self.with_context(skip_transfer=True)
#
#         res = super(PosMakePayment, self).check()  # Procesar el pago antes de continuar
#
#         StockPicking = self.env['stock.picking']
#         StockMove = self.env['stock.move']
#         StockMoveLine = self.env['stock.move.line']
#         StockLocation = self.env['stock.location']
#         StockLot = self.env['stock.lot']
#
#         # Obtener la orden activa desde el contexto
#         active_id = self.env.context.get('active_id')
#         if not active_id:
#             _logger.warning("❌ No se encontró una orden activa en el contexto.")
#             return res
#
#         order = self.env['pos.order'].browse(active_id)
#         _logger.info(f"🛒 Procesando orden: {order.name} (ID: {order.id}), Estado: {order.state}")
#
#         # 🔥 SOLO EJECUTAR SI ES UNA DEVOLUCIÓN 🔥
#         if not order.refunded_order_ids:
#             _logger.warning(f"❌ La orden {order.name} no es una devolución. No se ejecuta el proceso.")
#             return res
#
#         # 🔥 OBTENER ORDEN ORIGINAL DESDE EL BOTÓN "ÓRDENES REEMBOLSADAS" 🔥
#         original_order = order.refunded_order_ids[:1]
#         if not original_order:
#             _logger.warning(f"⚠ No se pudo obtener la orden original desde el botón inteligente.")
#             return res
#
#         _logger.info(f"📌 Orden Original Encontrada: {original_order.name} (ID: {original_order.id})")
#
#         original_picking = original_order.picking_ids.filtered(lambda p: p.state == 'done')
#         if not original_picking:
#             _logger.warning(f"⚠ La orden original {original_order.name} NO tiene recolecciones asociadas, SE OMITE.")
#             return res
#
#         # 🔥 MAPEAR RECOLECCIONES ORIGINALES ANTES DE LA EJECUCIÓN 🔥
#         original_picking_ids = original_picking.ids
#         _logger.info(f"📦 Recolecciones originales antes de la ejecución: {original_picking_ids}")
#
#         customer_location = StockLocation.search([('usage', '=', 'customer')], limit=1)
#         if not customer_location:
#             _logger.error("❌ ERROR: No se encontró la ubicación de clientes.")
#             raise ValidationError("No se encontró la ubicación de clientes.")
#
#         return_picking = StockPicking.create({
#             'partner_id': order.partner_id.id,
#             'picking_type_id': original_picking[0].picking_type_id.return_picking_type_id.id if original_picking else False,
#             'location_id': customer_location.id,
#             'location_dest_id': original_picking[0].picking_type_id.default_location_dest_id.id if original_picking else False,
#             'origin': f"RET/{order.name}",
#         })
#
#         _logger.info(f"✅ Albarán de devolución creado: {return_picking.name} (ID: {return_picking.id})")
#
#         for line in order.lines:
#             if line.product_id.type in ['product', 'consu']:
#                 move = StockMove.create({
#                     'name': f"Return {line.product_id.name}",
#                     'product_id': line.product_id.id,
#                     'product_uom_qty': abs(line.qty),
#                     'product_uom': line.product_id.uom_id.id,
#                     'picking_id': return_picking.id,
#                     'location_id': customer_location.id,
#                     'location_dest_id': return_picking.location_dest_id.id,
#                     'origin': f"RET/{order.name}",
#                 })
#                 _logger.info(f"✅ Movimiento de stock creado: {move.name} (ID: {move.id})")
#
#                 # 🔥 ASIGNAR NÚMERO DE LOTE SI EL PRODUCTO LO REQUIERE 🔥
#                 if line.product_id.tracking in ['lot', 'serial']:
#                     original_lot_name = None
#
#                     # Buscar lote en el picking original
#                     for original_move in original_picking.mapped('move_line_ids'):
#                         if original_move.product_id.id == line.product_id.id and original_move.lot_id:
#                             original_lot_name = original_move.lot_id.name
#                             break
#
#                     # Si no se encuentra el lote en la orden original, intentar buscarlo en `pack_lot_ids`
#                     if not original_lot_name:
#                         lot_name_from_pos = line.pack_lot_ids[:1].lot_name if line.pack_lot_ids else None
#                         if lot_name_from_pos:
#                             original_lot_name = lot_name_from_pos
#
#                     # Si no se encontró el lote, lanzar error
#                     if not original_lot_name:
#                         raise ValidationError(f"Debe proporcionar un número de lote/de serie para el producto:\n - [{line.product_id.default_code}] {line.product_id.display_name}")
#
#                     # Buscar el lote en `stock.lot`
#                     lot_record = StockLot.search([
#                         ('name', '=', original_lot_name),
#                         ('product_id', '=', line.product_id.id)
#                     ], limit=1)
#
#                     if not lot_record:
#                         raise ValidationError(f"No se encontró el lote '{original_lot_name}' en stock.lot para el producto: {line.product_id.display_name}")
#
#                     # Crear línea de movimiento con el lote asignado
#                     StockMoveLine.create({
#                         'move_id': move.id,
#                         'location_id': move.location_id.id,
#                         'location_dest_id': move.location_dest_id.id,
#                         'product_id': move.product_id.id,
#                         'qty_done': abs(line.qty),
#                         'product_uom_id': move.product_uom.id,
#                         'lot_id': lot_record.id,
#                         'lot_name': lot_record.name,
#                     })
#
#                     _logger.info(f"✅ Movimiento con lote asignado, Lote: {lot_record.name}")
#
#         return_picking.action_confirm()
#         return_picking.action_assign()
#         return_picking.button_validate()
#
#         _logger.info(f"✅ Picking validado: {return_picking.name} (ID: {return_picking.id})")
#
#         order.write({'picking_ids': [(4, return_picking.id)]})
#         _logger.info(f"✅ Orden {order.name} (ID: {order.id}) actualizada con picking {return_picking.id}")
#
#         # 🔥 MAPEAR RECOLECCIONES DESPUÉS DE LA EJECUCIÓN 🔥
#         all_pickings_after = original_order.picking_ids.ids
#         new_picking_ids = list(set(all_pickings_after) - set(original_picking_ids))
#         _logger.info(f"🚨 Recolecciones adicionales detectadas: {new_picking_ids}")
#
#         # 🔥 ELIMINAR RECOLECCIONES NUEVAS 🔥
#         if new_picking_ids:
#             pickings_to_delete = self.env['stock.picking'].browse(new_picking_ids).filtered(lambda p: p.state in ['waiting', 'confirmed'])
#             if pickings_to_delete:
#                 _logger.info(f"🗑 Eliminando {len(pickings_to_delete)} recolecciones creadas en la orden original.")
#                 pickings_to_delete.unlink()
#             else:
#                 _logger.info("✅ No se encontraron recolecciones en estado 'waiting' o 'confirmed' para eliminar.")
#
#         _logger.info("===== FIN DE MÉTODO pos.make.payment.check() =====")
#         return res

# import logging
# from odoo import models, fields, api
# from odoo.exceptions import ValidationError
#
# _logger = logging.getLogger(__name__)
#
#
# class PosMakePayment(models.TransientModel):
#     _inherit = 'pos.make.payment'
#
#     def check(self):
#         """
#         Sobrescribe el método check() de pos.make.payment para generar los movimientos de stock
#         después de que el pago de la devolución sea confirmado y gestionar estados de pickings.
#         """
#         _logger.info("===== EJECUTANDO MÉTODO pos.make.payment.check() =====")
#
#         # 🔥 PASAR CONTEXTO PARA EVITAR TRANSFERENCIAS 🔥
#         self = self.with_context(skip_transfer=True)
#
#         res = super(PosMakePayment, self).check()  # Procesar el pago antes de continuar
#
#         StockPicking = self.env['stock.picking']
#         StockMove = self.env['stock.move']
#         StockMoveLine = self.env['stock.move.line']
#         StockLocation = self.env['stock.location']
#         StockLot = self.env['stock.lot']
#
#         # Obtener la orden activa desde el contexto
#         active_id = self.env.context.get('active_id')
#         if not active_id:
#             _logger.warning("❌ No se encontró una orden activa en el contexto.")
#             return res
#
#         order = self.env['pos.order'].browse(active_id)
#         _logger.info(f"🛒 Procesando orden: {order.name} (ID: {order.id}), Estado: {order.state}")
#
#         # 🔥 SOLO EJECUTAR SI ES UNA DEVOLUCIÓN 🔥
#         if not order.refunded_order_ids:
#             _logger.warning(f"❌ La orden {order.name} no es una devolución. No se ejecuta el proceso.")
#             return res
#
#         original_order = order.refunded_order_ids[:1]
#         if not original_order:
#             _logger.warning(f"⚠ No se pudo obtener la orden original desde el botón inteligente.")
#             return res
#
#         _logger.info(f"📌 Orden Original Encontrada: {original_order.name} (ID: {original_order.id})")
#
#         original_picking = original_order.picking_ids.filtered(lambda p: p.state == 'done')
#         if not original_picking:
#             _logger.warning(f"⚠ La orden original {original_order.name} NO tiene recolecciones asociadas, SE OMITE.")
#             return res
#
#         original_picking_ids = original_picking.ids
#         _logger.info(f"📦 Recolecciones originales antes de la ejecución: {original_picking_ids}")
#
#         customer_location = StockLocation.search([('usage', '=', 'customer')], limit=1)
#         if not customer_location:
#             _logger.error("❌ ERROR: No se encontró la ubicación de clientes.")
#             raise ValidationError("No se encontró la ubicación de clientes.")
#
#         return_picking = StockPicking.create({
#             'partner_id': order.partner_id.id,
#             'picking_type_id': original_picking[0].picking_type_id.return_picking_type_id.id if original_picking else False,
#             'location_id': customer_location.id,
#             'location_dest_id': original_picking[0].picking_type_id.default_location_dest_id.id if original_picking else False,
#             'origin': f"RET/{order.name}",
#         })
#
#         _logger.info(f"✅ Albarán de devolución creado: {return_picking.name} (ID: {return_picking.id})")
#
#         for line in order.lines:
#             if line.product_id.type in ['product', 'consu']:
#                 move = StockMove.create({
#                     'name': f"Return {line.product_id.name}",
#                     'product_id': line.product_id.id,
#                     'product_uom_qty': abs(line.qty),
#                     'product_uom': line.product_id.uom_id.id,
#                     'picking_id': return_picking.id,
#                     'location_id': customer_location.id,
#                     'location_dest_id': return_picking.location_dest_id.id,
#                     'origin': f"RET/{order.name}",
#                 })
#                 _logger.info(f"✅ Movimiento de stock creado: {move.name} (ID: {move.id})")
#
#                 # 🔥 ASIGNAR NÚMERO DE LOTE SI EL PRODUCTO LO REQUIERE 🔥
#                 if line.product_id.tracking in ['lot', 'serial']:
#                     original_lot_name = None
#
#                     # Buscar lote en el picking original
#                     for original_move in original_picking.mapped('move_line_ids'):
#                         if original_move.product_id.id == line.product_id.id and original_move.lot_id:
#                             original_lot_name = original_move.lot_id.name
#                             break
#
#                     # Intentar buscar el lote en `pack_lot_ids` si no se encuentra en el picking original
#                     if not original_lot_name:
#                         lot_name_from_pos = line.pack_lot_ids[:1].lot_name if line.pack_lot_ids else None
#                         if lot_name_from_pos:
#                             original_lot_name = lot_name_from_pos
#
#                     if not original_lot_name:
#                         raise ValidationError(f"Debe proporcionar un número de lote/de serie para el producto:\n - [{line.product_id.default_code}] {line.product_id.display_name}")
#
#                     lot_record = StockLot.search([
#                         ('name', '=', original_lot_name),
#                         ('product_id', '=', line.product_id.id)
#                     ], limit=1)
#
#                     if not lot_record:
#                         raise ValidationError(f"No se encontró el lote '{original_lot_name}' en stock.lot para el producto: {line.product_id.display_name}")
#
#                     StockMoveLine.create({
#                         'move_id': move.id,
#                         'location_id': move.location_id.id,
#                         'location_dest_id': move.location_dest_id.id,
#                         'product_id': move.product_id.id,
#                         'qty_done': abs(line.qty),
#                         'product_uom_id': move.product_uom.id,
#                         'lot_id': lot_record.id,
#                         'lot_name': lot_record.name,
#                     })
#
#                     _logger.info(f"✅ Movimiento con lote asignado, Lote: {lot_record.name}")
#
#         return_picking.action_confirm()
#         return_picking.action_assign()
#         return_picking.button_validate()
#
#         _logger.info(f"✅ Picking validado: {return_picking.name} (ID: {return_picking.id})")
#
#         order.write({'picking_ids': [(4, return_picking.id)]})
#
#         # 🔥 ELIMINAR RECOLECCIONES NUEVAS 🔥
#         new_picking_ids = list(set(original_order.picking_ids.ids) - set(original_picking_ids))
#         pickings_to_delete = StockPicking.browse(new_picking_ids).filtered(lambda p: p.state in ['waiting', 'confirmed'])
#         if pickings_to_delete:
#             _logger.info(f"🗑 Eliminando {len(pickings_to_delete)} recolecciones creadas en la orden original.")
#             pickings_to_delete.unlink()
#         return res

import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    def check(self):
        """
        Sobrescribe el método check() de pos.make.payment para generar los movimientos de stock
        después de que el pago de la devolución sea confirmado y gestionar estados de pickings.
        """
        _logger.info("===== EJECUTANDO MÉTODO pos.make.payment.check() =====")

        self = self.with_context(skip_transfer=True)
        res = super(PosMakePayment, self).check()

        StockPicking = self.env['stock.picking']
        StockMove = self.env['stock.move']
        StockMoveLine = self.env['stock.move.line']
        StockLocation = self.env['stock.location']
        StockLot = self.env['stock.lot']

        active_id = self.env.context.get('active_id')
        if not active_id:
            _logger.warning("❌ No se encontró una orden activa en el contexto.")
            return res

        order = self.env['pos.order'].browse(active_id)
        _logger.info(f"🛒 Procesando orden: {order.name} (ID: {order.id}), Estado: {order.state}")

        if not order.refunded_order_ids:
            _logger.warning(f"❌ La orden {order.name} no es una devolución. No se ejecuta el proceso.")
            return res

        original_order = order.refunded_order_ids[:1]
        if not original_order:
            _logger.warning(f"⚠ No se pudo obtener la orden original desde el botón inteligente.")
            return res

        _logger.info(f"📌 Orden Original Encontrada: {original_order.name} (ID: {original_order.id})")

        original_picking = original_order.picking_ids.filtered(lambda p: p.state == 'done')
        if not original_picking:
            _logger.warning(f"⚠ La orden original {original_order.name} NO tiene recolecciones asociadas, SE OMITE.")
            return res

        original_picking_ids = original_picking.ids
        _logger.info(f"📦 Recolecciones originales antes de la ejecución: {original_picking_ids}")

        customer_location = StockLocation.search([('usage', '=', 'customer')], limit=1)
        if not customer_location:
            _logger.error("❌ ERROR: No se encontró la ubicación de clientes.")
            raise ValidationError("No se encontró la ubicación de clientes.")

        # 🔥 Crear dos pickings: uno para productos normales y otro para motos 🔥
        return_picking = None
        return_picking_motos = None

        for line in order.lines:
            if line.product_id.type in ['product', 'consu']:
                is_moto = bool(line.product_id.x_studio_es_moto_1)

                if is_moto:
                    if not return_picking_motos:
                        return_picking_motos = StockPicking.create({
                            'partner_id': order.partner_id.id,
                            'picking_type_id': original_picking[0].picking_type_id.return_picking_type_id.id if original_picking else False,
                            'location_id': customer_location.id,
                            'location_dest_id': original_picking[0].picking_type_id.default_location_dest_id.id if original_picking else False,
                            'origin': f"RET-MOTOS/{order.name}",
                        })
                        _logger.info(f"🏍 Picking de devolución de motos creado: {return_picking_motos.name} (ID: {return_picking_motos.id})")

                    picking = return_picking_motos
                else:
                    if not return_picking:
                        return_picking = StockPicking.create({
                            'partner_id': order.partner_id.id,
                            'picking_type_id': original_picking[0].picking_type_id.return_picking_type_id.id if original_picking else False,
                            'location_id': customer_location.id,
                            'location_dest_id': original_picking[0].picking_type_id.default_location_dest_id.id if original_picking else False,
                            'origin': f"RET/{order.name}",
                        })
                        _logger.info(f"✅ Albarán de devolución creado: {return_picking.name} (ID: {return_picking.id})")

                    picking = return_picking

                move = StockMove.create({
                    'name': f"Return {line.product_id.name}",
                    'product_id': line.product_id.id,
                    'product_uom_qty': abs(line.qty),
                    'product_uom': line.product_id.uom_id.id,
                    'picking_id': picking.id,
                    'location_id': customer_location.id,
                    'location_dest_id': picking.location_dest_id.id,
                    'origin': picking.origin,
                })
                _logger.info(f"✅ Movimiento de stock creado: {move.name} (ID: {move.id})")

                if line.product_id.tracking in ['lot', 'serial']:
                    original_lot_name = None

                    for original_move in original_picking.mapped('move_line_ids'):
                        if original_move.product_id.id == line.product_id.id and original_move.lot_id:
                            original_lot_name = original_move.lot_id.name
                            break

                    lot_name_from_pos = line.pack_lot_ids[:1].lot_name if line.pack_lot_ids else None
                    if not original_lot_name and lot_name_from_pos:
                        original_lot_name = lot_name_from_pos

                    if not original_lot_name:
                        raise ValidationError(f"Debe proporcionar un número de lote/de serie para el producto:\n - [{line.product_id.default_code}] {line.product_id.display_name}")

                    lot_record = StockLot.search([
                        ('name', '=', original_lot_name),
                        ('product_id', '=', line.product_id.id)
                    ], limit=1)

                    if not lot_record:
                        raise ValidationError(f"No se encontró el lote '{original_lot_name}' en stock.lot para el producto: {line.product_id.display_name}")

                    StockMoveLine.create({
                        'move_id': move.id,
                        'location_id': move.location_id.id,
                        'location_dest_id': move.location_dest_id.id,
                        'product_id': move.product_id.id,
                        'qty_done': abs(line.qty),
                        'product_uom_id': move.product_uom.id,
                        'lot_id': lot_record.id,
                        'lot_name': lot_record.name,
                    })

                    _logger.info(f"✅ Movimiento con lote asignado, Lote: {lot_record.name}")

        if return_picking:
            return_picking.action_confirm()
            return_picking.action_assign()
            return_picking.button_validate()
            _logger.info(f"✅ Picking validado: {return_picking.name} (ID: {return_picking.id})")
            order.write({'picking_ids': [(4, return_picking.id)]})

        if return_picking_motos:
            return_picking_motos.action_confirm()
            return_picking_motos.action_assign()
            return_picking_motos.button_validate()
            _logger.info(f"🏍 Picking de motos validado: {return_picking_motos.name} (ID: {return_picking_motos.id})")
            order.write({'picking_ids': [(4, return_picking_motos.id)]})

        new_picking_ids = list(set(original_order.picking_ids.ids) - set(original_picking_ids))
        pickings_to_delete = StockPicking.browse(new_picking_ids).filtered(lambda p: p.state in ['waiting', 'confirmed'])
        if pickings_to_delete:
            _logger.info(f"🗑 Eliminando {len(pickings_to_delete)} recolecciones creadas en la orden original.")
            pickings_to_delete.unlink()

        return res

class PosOrder(models.Model):
    _inherit = "pos.order"

    def refund(self):
        """
        Sobrescribe el método refund() de pos.order para verificar que todos los pickings asociados
        a la orden original estén en estado 'done' antes de permitir la devolución.
        """
        _logger.info(f"===== EJECUTANDO MÉTODO pos.order.refund() PARA {self.name} =====")

        for order in self:
            _logger.info(f"🔎 Verificando pickings de la orden {order.name} antes de reembolsar...")

            # Obtener todos los pickings relacionados con la orden
            pickings = order.picking_ids

            if not pickings:
                _logger.warning(f"⚠ La orden {order.name} NO tiene recolecciones asociadas. Se permite la devolución.")
                continue  # Permitir la devolución si no hay pickings asociados

            # Filtrar pickings que NO estén en estado 'done'
            pending_pickings = pickings.filtered(lambda p: p.state != 'done')

            if pending_pickings:
                _logger.error(f"❌ ERROR: La orden {order.name} tiene {len(pending_pickings)} pickings en estado pendiente.")
                raise ValidationError(
                    f"No se puede procesar la devolución porque hay {len(pending_pickings)} albaranes asociados "
                    f"a la orden {order.name} que aún no están en estado 'Hecho'.\n\n"
                    "Por favor, finaliza los movimientos de stock antes de procesar la devolución."
                )

            _logger.info(f"✅ Todos los pickings de la orden {order.name} están en estado 'done'. Procediendo con la devolución.")

        return super(PosOrder, self).refund()