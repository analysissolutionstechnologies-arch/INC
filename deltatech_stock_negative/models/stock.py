# # ©  2008-2021 Deltatech
# # See README.rst file on addons root folder for license details
#
#
# from odoo import _, models
# from odoo.exceptions import UserError
#
#
# class StockQuant(models.Model):
#     _inherit = "stock.quant"
#
#     def _get_available_quantity(
#         self, product_id, location_id, lot_id=None, package_id=None, owner_id=None, strict=False, allow_negative=False
#     ):
#         res = super()._get_available_quantity(
#             product_id=product_id,
#             location_id=location_id,
#             lot_id=lot_id,
#             package_id=package_id,
#             owner_id=owner_id,
#             strict=strict,
#             allow_negative=allow_negative,
#         )
#         company = self.company_id or self.env.company
#         if not company.no_negative_stock:
#             return res
#
#         if (
#             location_id
#             and not location_id.allow_negative_stock
#             and round(res, 2) < 0.0
#             and location_id.usage == "internal"
#         ):
#             err = _(
#                 "You have chosen to avoid negative stock. %(lot_qty)s pieces of %(product_name)s are remaining in location %(location_name)s. "
#                 "Please adjust your quantities or correct your stock with an inventory adjustment."
#             ) % {
#                 "lot_qty": res,
#                 "product_name": product_id.name,
#                 "location_name": location_id.name,
#             }
#             raise UserError(err)
#         return res


from odoo import _, models
from odoo.exceptions import UserError


class StockQuant(models.Model):
    _inherit = "stock.quant"

    def _get_available_quantity(
        self, product_id, location_id, lot_id=None, package_id=None, owner_id=None, strict=False, allow_negative=False
    ):
        res = super()._get_available_quantity(
            product_id=product_id,
            location_id=location_id,
            lot_id=lot_id,
            package_id=package_id,
            owner_id=owner_id,
            strict=strict,
            allow_negative=allow_negative,
        )
        company = self.company_id or self.env.company
        if not company.no_negative_stock:
            return res

        if product_id.tracking == 'serial' and lot_id:
            if (
                location_id
                and not location_id.allow_negative_stock
                and round(res, 2) < 0.0
                and location_id.usage == "internal"
            ):
                # Buscar líneas de movimiento que tienen este producto, ubicación y lote (número de serie)
                move_lines = self.env['stock.move.line'].search([
                    ('product_id', '=', product_id.id),
                    ('location_id', '=', location_id.id),
                    ('lot_id', '=', lot_id.id),
                    ('state', '=', 'assigned'),
                ])
                for ml in move_lines:
                    ml.move_id._do_unreserve()

                # Recalcular disponibilidad
                res = super()._get_available_quantity(
                    product_id=product_id,
                    location_id=location_id,
                    lot_id=lot_id,
                    package_id=package_id,
                    owner_id=owner_id,
                    strict=strict,
                    allow_negative=allow_negative,
                )

                if round(res, 2) < 0.0:
                    err = _(
                        "Atención: El artículo %(product_name)s con serie %(serial)s no está disponible en esta ubicación. Antes de facturar, por favor revisa la existencia en otras ubicaciones."
                    ) % {
                        "serial": lot_id.name,
                        "product_name": product_id.name,
                        "location_name": location_id.name,
                    }
                    raise UserError(err)

            return res

        # Control para productos sin serie
        if (
            location_id
            and not location_id.allow_negative_stock
            and round(res, 2) < 0.0
            and location_id.usage == "internal"
        ):
            err = _(
                "Atención: El artículo %(product_name)s no está disponible en esta ubicación. Antes de facturar, por favor revisa la existencia en otras ubicaciones."
            ) % {
                "lot_qty": res,
                "product_name": product_id.name,
                "location_name": location_id.name,
            }
            raise UserError(err)

        return res

