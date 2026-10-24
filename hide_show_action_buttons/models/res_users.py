from odoo import api, models, fields, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    hide_all_export = fields.Boolean(string='Hide All Export')
    hide_export_model_ids = fields.Many2many('ir.model', string='Hide Export for Specific Model', relation='hide_export_button_ir_model_rel')

    hide_all_archive = fields.Boolean(string='Hide All Archive')
    hide_archive_model_ids = fields.Many2many('ir.model', string='Hide Archive for Specific Model', relation='hide_archive_button_ir_model_rel')

    hide_all_duplicate = fields.Boolean(string='Hide All Duplicate')
    hide_duplicate_model_ids = fields.Many2many('ir.model', string='Hide Duplicate for Specific Model', relation='hide_duplicate_button_ir_model_rel')

    hide_all_create = fields.Boolean(string='Hide All Create')
    hide_create_model_ids = fields.Many2many('ir.model', string='Hide Create for Specific Model', relation='hide_create_button_ir_model_rel')

    hide_all_edit = fields.Boolean(string='Hide All Edit')
    hide_edit_model_ids = fields.Many2many('ir.model', string='Hide Edit for Specific Model', relation='hide_edit_button_ir_model_rel')

    hide_all_delete = fields.Boolean(string='Hide All Delete')
    hide_delete_model_ids = fields.Many2many('ir.model', string='Hide Delete for Specific Model', relation='hide_delete_button_ir_model_rel')

    hide_all_print = fields.Boolean(string='Hide All Print')
    hide_print_model_ids = fields.Many2many('ir.model', string='Hide Print for Specific Model', relation='hide_print_button_ir_model_rel')

    hide_all_import = fields.Boolean(string='Hide All Import')
    hide_import_model_ids = fields.Many2many('ir.model', string='Hide Import for Specific Model', relation='hide_import_button_ir_model_rel')

    def is_export_enable(self, model_name):
        return self.is_button_enable(model_name, 'export')

    def is_archive_enable(self, model_name):
        return self.is_button_enable(model_name, 'archive')

    def is_duplicate_enable(self, model_name):
        return self.is_button_enable(model_name, 'duplicate')

    def is_create_enable(self, model_name):
        return self.is_button_enable(model_name, 'create')

    def is_edit_enable(self, model_name):
        return self.is_button_enable(model_name, 'edit')

    def is_delete_enable(self, model_name):
        return self.is_button_enable(model_name, 'delete')

    def is_print_enable(self, model_name):
        return self.is_button_enable(model_name, 'print')

    def is_import_enable(self, model_name):
        return self.is_button_enable(model_name, 'import')

    @api.model
    def is_button_enable(self, model_name, button_name):
        """
        Check if button is enable or not
        :param model_name: string
        :param button_name: string
        :return: boolean
        """
        disable = eval('self.hide_all_%s or \'%s\' in self.hide_%s_model_ids.mapped("model")' % (button_name, model_name, button_name))
        return not disable

