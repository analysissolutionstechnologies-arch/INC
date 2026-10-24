# from odoo import _, api, models
#
#
# class IrAttachment(models.Model):
#     _inherit = "ir.attachment"
#
#     @api.model_create_multi
#     def create(self, vals_list):
#         res = super(IrAttachment, self).create(vals_list)
#         res.generate_access_token()
#         return res
#
#     def write(self, values):
#         res = super().write(values)
#         for rec in self.filtered(lambda rec: not rec.access_token):
#             rec.generate_access_token()
#         return res
#
#     @api.model
#     def generate_access_token_fix(self):
#         query = f"""
#             SELECT
#                 id
#             FROM
#                 ir_attachment ia
#             WHERE
#                 access_token IS NULL
#         """
#         self.env.cr.execute(query)
#         self.browse([i[0] for i in self.env.cr.fetchall()]).generate_access_token()

from odoo import _, api, models


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.model_create_multi
    def create(self, vals_list):
        """
        Sobrescribe el método `create` para generar tokens de acceso
        automáticamente al crear nuevos adjuntos.
        """
        attachments = super(IrAttachment, self).create(vals_list)
        attachments.generate_access_token()
        return attachments

    def write(self, values):
        """
        Sobrescribe el método `write` para generar tokens de acceso
        automáticamente para los registros que no tienen uno.
        """
        res = super().write(values)
        self.filtered(lambda rec: not rec.access_token).generate_access_token()
        return res

    @api.model
    def generate_access_token_fix(self):
        """
        Genera tokens de acceso para todos los adjuntos que no lo tienen.
        """
        query = """
            SELECT id
            FROM ir_attachment
            WHERE access_token IS NULL
        """
        self.env.cr.execute(query)
        attachment_ids = [record[0] for record in self.env.cr.fetchall()]
        if attachment_ids:
            self.browse(attachment_ids).generate_access_token()
