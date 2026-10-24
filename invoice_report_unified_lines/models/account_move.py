# -*- coding: utf-8 -*-

from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def get_lines_for_report(self):
        self.ensure_one()

        lines = self.invoice_line_ids.filtered(lambda l: l.display_type == 'product')
        moto_lines = lines.filtered(lambda l: l.product_id.x_studio_es_moto_1)
        if not moto_lines:
            return lines

        moto_line = moto_lines[0]
        sum_lines = {
            'precio': 0.0,
            'total': 0.0,
            'impuestos': [],
        }

        # Adaptado de tu_funcion_para_modificar_lineas: sumar todas las líneas y unificar en la línea moto.
        for line in lines:
            precio = line.price_unit * line.quantity
            total = line.price_total
            sum_lines['precio'] += precio
            sum_lines['total'] += total

            for tax in line.tax_ids:
                nombre = tax.name
                monto_gravable = line.price_subtotal
                monto_impuesto = line.price_total - line.price_subtotal

                impuesto_existente = next(
                    (imp for imp in sum_lines['impuestos'] if imp['nombre_corto'] == nombre),
                    None,
                )
                if impuesto_existente:
                    impuesto_existente['monto_impuesto'] += monto_impuesto
                    impuesto_existente['monto_gravable'] += monto_gravable
                else:
                    sum_lines['impuestos'].append({
                        'nombre_corto': nombre,
                        'codigo_unidad_gravable': '1',
                        'monto_gravable': monto_gravable,
                        'monto_impuesto': monto_impuesto,
                    })

        result_lines = [{
            'name': moto_line.name,
            'quantity': moto_line.quantity,
            'price_unit': sum_lines['precio'] / moto_line.quantity if moto_line.quantity else sum_lines['precio'],
            'price': sum_lines['precio'],
            'total': sum_lines['total'],
            'impuestos': sum_lines['impuestos'],
            'is_unified': True,
            'moto_ref': moto_line.product_id.default_code or '',
        }]

        for line in lines:
            if line == moto_line:
                continue
            result_lines.append({
                'name': line.name,
                'quantity': line.quantity,
                'price_unit': 0.0,
                'price': 0.0,
                'total': 0.0,
                'impuestos': [{
                    'nombre_corto': tax.name,
                } for tax in line.tax_ids],
            })

        return result_lines
