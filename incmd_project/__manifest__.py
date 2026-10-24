{
    'name': 'Servicio Cliente INC',
    'version': '17.0.1.0.0',
    'category': 'Helpdesk',
    'description': """
        Personalización de modulo servicio al cliente.
    """,
    'summary': """
        Personalización de modulo servicio al cliente.
    """,
    "author": "Incomel",
    "license": "AGPL-3",
    'depends': ['project', 'website'],
    'data': [
        'views/service_project_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}