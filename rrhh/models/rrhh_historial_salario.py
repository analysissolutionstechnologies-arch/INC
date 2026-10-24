# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, AccessError

class rrhh_historial_salario(models.Model):
    _name = "rrhh.historial_salario"
    _order = "fecha asc"

    salario = fields.Float('Salario', required=True)
    fecha = fields.Date('Fecha', required=True)
    contrato_id = fields.Many2one('hr.contract','Contato')
