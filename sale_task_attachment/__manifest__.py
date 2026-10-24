# sale_task_attachment/__manifest__.py
{
    'name': 'Sale Task Attachments',
    'version': '17.0',
    'category': 'Sales',
    'summary': 'Show sale order attachments in task',
    'description': """
        This module allows you to view attachments from the sale order (related via x_studio_adjuntos) directly from the task related to the sale order.
    """,
    'depends': ['sale_management', 'project'],
    'data': [
        'views/project_task_views.xml',
    ],
    'installable': True,
    'application': False,
}
