from odoo import models, fields, api
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allowed_attachment_extensions = fields.Char(
        string='Extensiones permitidas para adjuntos',
        config_parameter='custom_attachment.allowed_extensions',
        help='Ingrese las extensiones permitidas separadas por coma (ej: .png, .jpg, .pdf)'
    )
    restricted_attachment_models = fields.Many2many(
        comodel_name='ir.model',
        string='Modelos donde se aplican: Extensiones permitidas para adjuntos',
        help='Seleccione los modelos en los que se aplicará esta configuración de extensiones. Si no se selecciona ninguno, se aplicará a todos los modelos.',
    )

    # @api.constrains('allowed_attachment_extensions')
    # def _check_allowed_extensions(self):
    #     for record in self:
    #         if record.allowed_attachment_extensions:
    #             extensions = [ext.strip().lower() for ext in record.allowed_attachment_extensions.split(',') if ext.strip()]
    #             for ext in extensions:
    #                 if not ext.startswith('.'):
    #                     raise UserError(f'La extensión "{ext}" debe comenzar con un punto (ej: .png)')

    # @api.model
    # def get_values(self):
    #     res = super().get_values()
    #     param_model = self.env['ir.model']
    #     # Modelos por defecto si no hay configuracion
    #     default_model_names = ['sale.order', 'project.task', 'helpdesk.ticket']
    #     config_param = self.env['ir.config_parameter'].sudo()
    #     # Verificar si el parametro existe. Si no existe, es la primera vez (usar defaults).
    #     # Si existe pero esta vacio, el usuario lo guardo vacio a proposito (no usar defaults).
    #     stored = config_param.get_param('custom_attachment.restricted_models')
    #     if stored is not False and stored is not None:
    #         model_names = [m.strip() for m in stored.split(',') if m.strip()]
    #     else:
    #         model_names = default_model_names
    #     model_ids = param_model.sudo().search([('model', 'in', model_names)]).ids
    #     res['restricted_attachment_models'] = [(6, 0, model_ids)]
    #     return res

    # def set_values(self):
    #     config_param = self.env['ir.config_parameter'].sudo()
    #     if self.restricted_attachment_models:
    #         model_names = ','.join(self.restricted_attachment_models.mapped('model'))
    #     else:
    #         model_names = ''
    #     # Siempre guardamos el parametro (aunque sea vacio) para que get_values sepa que ya se configuro
    #     config_param.set_param('custom_attachment.restricted_models', model_names)
    #     super().set_values()