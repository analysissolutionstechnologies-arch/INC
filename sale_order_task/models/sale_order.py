from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    task_ids = fields.One2many('project.task', compute='_compute_task_ids', string='Tareas Relacionadas')
    tasks_info = fields.Char(string='Tareas y Estados', compute='_compute_tasks_info')

    def _compute_task_ids(self):
        for order in self:
            tasks = self.env['project.task'].search([('x_studio_pedido', '=', order.id)])
            order.task_ids = tasks

    def _compute_tasks_info(self):
        for order in self:
            tasks_info_list = []
            for task in order.task_ids:
                tasks_info_list.append(f"{task.name} - {task.stage_id.name}")
            order.tasks_info = "; ".join(tasks_info_list) if tasks_info_list else ''
