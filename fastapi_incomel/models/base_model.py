# # -*- coding:utf-8 -*-
#
# from odoo import models
#
#
# class Base(models.AbstractModel):
#     _inherit = "base"
#
#     def get_field_binary(self, res_field):
#         query = f"""
#             SELECT
#                 access_token,
#                 mimetype
#             FROM
#                 ir_attachment ia
#             WHERE
#                 ia.res_id in ({', '.join(map(str, self.ids))})
#                 AND ia.res_model = '{self._name}'
#                 AND ia.res_field = '{res_field}'
#                 AND access_token IS NOT NULL
#         """
#         self.env.cr.execute(query)
#         return self.env.cr.fetchone()
#
#     def get_attachments(self):
#         query = f"""
#             SELECT
#                 id,
#                 access_token,
#                 mimetype,
#                 name
#             FROM
#                 ir_attachment ia
#             WHERE
#                 ia.res_id in ({','.join(map(str, self.ids))})
#                 AND ia.res_model = '{self._name}'
#                 AND access_token IS NOT NULL
#         """
#         self.env.cr.execute(query)
#         datas = self.env.cr.fetchall()
#         if not datas:
#             return None
#         result = []
#         base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", "")
#         for attachment in datas:
#             result.append(
#                 {
#                     "id": attachment[0],
#                     "url": (
#                         base_url + "/api/v1/file?token=" + attachment[1]
#                         if attachment[2] not in ["video/mp4", "video/3gpp"]
#                         else base_url + "/api/v1/video?token=" + attachment[1]
#                     ),
#                     "display_name": attachment[3],
#                     "mimetype": attachment[2],
#                 }
#             )
#         return result

# -*- coding:utf-8 -*-

from odoo import models


class Base(models.AbstractModel):
    _inherit = "base"

    def get_field_binary(self, res_field):
        """
        Obtiene el token de acceso y el tipo MIME de un campo binario
        relacionado con los registros actuales.
        """
        query = """
            SELECT
                access_token,
                mimetype
            FROM
                ir_attachment
            WHERE
                res_id = ANY(%s)
                AND res_model = %s
                AND res_field = %s
                AND access_token IS NOT NULL
        """
        self.env.cr.execute(query, (self.ids, self._name, res_field))
        return self.env.cr.fetchone()

    def get_attachments(self):
        """
        Obtiene todos los adjuntos relacionados con los registros actuales,
        incluyendo su token de acceso, MIME, y nombre.
        """
        query = """
            SELECT
                id,
                access_token,
                mimetype,
                name
            FROM
                ir_attachment
            WHERE
                res_id = ANY(%s)
                AND res_model = %s
                AND access_token IS NOT NULL
        """
        self.env.cr.execute(query, (self.ids, self._name))
        datas = self.env.cr.fetchall()

        if not datas:
            return None

        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", "")
        return [
            {
                "id": attachment[0],
                "url": (
                    f"{base_url}/api/v1/file?token={attachment[1]}"
                    if attachment[2] not in ["video/mp4", "video/3gpp"]
                    else f"{base_url}/api/v1/video?token={attachment[1]}"
                ),
                "display_name": attachment[3],
                "mimetype": attachment[2],
            }
            for attachment in datas
        ]
