# -*- coding: utf-8 -*-

from odoo import models, fields, api

class rrhh_planilla(models.Model):
    _name = 'rrhh.planilla'
    _description = 'Planilla'

    name = fields.Char('Nombre', size=40, required=True)
    descripcion = fields.Char('Descripción', size=120)
    columna_id = fields.One2many('rrhh.planilla.columna', 'planilla_id', 'Columnas')

class rrhh_planilla_columna(models.Model):
    _name = 'rrhh.planilla.columna'
    _description = 'Columna de planilla'
    _order = 'sequence, name'

    name = fields.Char('Nombre', size=40, required=True)
    sequence = fields.Integer('Secuencia', required=True, index=True, default=5)
    regla_id = fields.Many2many('hr.salary.rule', id1='columna_id',id2='regla_id', string='Reglas')
    entrada_id = fields.Many2many('hr.payslip.input.type',id1='columna_id',id2='entrada_id',string='Entradas')
    planilla_id = fields.Many2one('rrhh.planilla', 'Planilla', required=False)
    sumar = fields.Boolean('Sumar en liquido a recibir', help="Seleccionar si se desea que se tome en cuenta en la suma del liquido a recibir.")