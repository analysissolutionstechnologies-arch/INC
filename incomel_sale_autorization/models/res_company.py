#


from odoo import api, fields, models, _
from odoo import models, fields
from datetime import datetime
import requests


class ResCompany(models.Model):

    _inherit = "res.company"
   
    url_netfinance_conect = fields.Char(string=u"URL NETFINANCE", help="URL NETFINANCE", default="https://testnf.incomel.com.gt/NetFinance/api/")
    puerto_netfinance = fields.Char(string=u"PUERTO NETFINANCE", help="PUERTO NETFINANCE" , default="8443")
    vpn_netfinance = fields.Char(string=u"VPN NETFINANCE", help="VPN NETFINANCE") 
    selection_url_netfinance = fields.Selection([('prod', 'Producción'), ('dev', 'Desarrollo')], string='URL', default='dev')
    ultimo_refresh_token_netfinance = fields.Datetime(string="netfinance Refresh Token" , format="%Y-%m-%d %H:%M%S" ,
                                           default=fields.Datetime.now) 
    cliente_netfinance = fields.Char(string="CLIENTE NETFINANCE" , default="basicUser2024")
    credencial_netfinance = fields.Char(string="Credencial NETFINANCE" , default="Acc3S04r")
    token_netfinance = fields.Char(string="Token NETFINANCE", default="JIUzI1NiIsInR5cCI6IkpXVCJ9dGVzdF90b2tlbg7")
    hash_key_netfinance =  fields.Char(string="Hash Key NETFINANCE", default="d364db7e8c1b3a7168a2aafcdf45bb7")


