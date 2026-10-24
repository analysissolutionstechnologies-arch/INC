#


from odoo import api, fields, models, _
from odoo import models, fields
from datetime import datetime
import requests


class ResPartner(models.Model):

    _inherit = "res.partner"
   
    partner_idPersona = fields.Char(string="Id Persona")
    municipio_id = fields.Many2one( 'res.municipiogt',string="Municipio")
    zona_id = fields.Many2one( 'res.zonagt',string="Zona")
    colonia_id = fields.Many2one( 'res.coloniagt',string="Colonia")
    state_id = fields.Many2one( 'res.country.state',string="Departamento")
    documento_personal_identificacion = fields.Char('DPI')

class Resmunicipio(models.Model):

    _name = "res.municipiogt"

    name = fields.Char(string="Municipio")
    code = fields.Char(string="Codigo")
    state_id = fields.Many2one( 'res.country.state',string="Departamento")


class Reszona(models.Model):
    _name = "res.zonagt"

    name = fields.Char(string="Zona")
    code = fields.Char(string="Codigo")
    municipio_id = fields.Many2one( 'res.municipiogt',string="Municipio")
    state_id = fields.Many2one( 'res.country.state',string="Departamento")


class Rescolonia(models.Model):
    _name = "res.coloniagt"

    name = fields.Char(string="Colonia")
    code = fields.Char(string="Codigo")
    zona_id = fields.Many2one( 'res.zonagt',string="Zona")
    municipio_id = fields.Many2one( 'res.municipiogt',string="Municipio")
    state_id = fields.Many2one( 'res.country.state',string="Departamento")