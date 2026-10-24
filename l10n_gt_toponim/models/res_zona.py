#


from odoo import api, fields, models, _
from odoo import models, fields
from datetime import datetime
import requests




class Reszona(models.Model):
    _name = "res.zonagt"

    name = fields.Char(string="Zona")
    code = fields.Char(string="Codigo")
    municipio_id = fields.Many2one( 'res.municipiogt',string="Municipio")
    state_id = fields.Many2one( 'res.country.state',string="Departamento"  , related="municipio_id.state_id")
    ID_SECTOR = fields.Integer( string="Sector" , unique=True)
    ID_ZONA = fields.Integer()

    ID_CIUDAD = fields.Integer()
    ID_TIPO_SECTOR = fields.Integer()
    CMP_NOMBRE_SECTOR = fields.Char()
    CMP_FECHA_INGRESO_SECTOR = fields.Char()
    CMP_ESTADO_SECTOR = fields.Char()
    Cmp_Activo = fields.Char()

# ID_SECTOR	ID_ZONA	ID_TIPO_SECTOR	ID_CIUDAD	CMP_NOMBRE_SECTOR	CMP_FECHA_INGRESO_SECTOR	CMP_ESTADO_SECTOR	Cmp_Activo
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('code', operator, name)]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()