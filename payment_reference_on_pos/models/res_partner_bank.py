# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResBank(models.Model):
    _inherit = 'res.bank'

    @api.model
    def get_bank_ids(self, bank_ids):
        bank_records = self.search([('id', 'in', bank_ids)])
        return bank_records.read(['name', 'bic'])  # Ajusta los campos según lo que necesites

    