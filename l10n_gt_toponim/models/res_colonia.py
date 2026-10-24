#


from odoo import api, fields, models, _
from odoo import models, fields
from datetime import datetime
import requests


class Rescolonia(models.Model):
    _name = "res.coloniagt"

    name = fields.Char(string="Colonia")
    code = fields.Char(string="Codigo")
    zona_id = fields.Many2one( 'res.zonagt',string="Zona")
    municipio_id = fields.Many2one( 'res.municipiogt',string="Municipio")
    state_id = fields.Many2one( 'res.country.state',string="Departamento" , related="municipio_id.state_id")

    # ID_BARRIO	ID_PAIS	ID_REGION	ID_CIUDAD	ID_SECTOR	CMP_DESCRIPCION_BARRIO	CMP_FECHA_INGRESO	Cmp_Activo
    ID_BARRIO = fields.Integer( string="Barrio" , unique=True)
    ID_PAIS = fields.Integer()
    ID_REGION = fields.Integer()
    ID_CIUDAD = fields.Integer()
    ID_SECTOR = fields.Integer()
    CMP_DESCRIPCION_BARRIO = fields.Char()
    CMP_FECHA_INGRESO = fields.Char()
    Cmp_Activo = fields.Char()