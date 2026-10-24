{
    'name': 'Tickets Soporte Motivos',
    'version': '17.0.1.0.0',
    'category': 'Helpdesk',
    'description': """
        Personalización de formulario de soporte técnico sistemas.
    """,
    'summary': """
        Agrega campo select personalizado solo al formulario de Soporte Técnico Sistemas.
    """,
    "author": "Incomel",
    "license": "AGPL-3",
    'depends': ['website', 'website_helpdesk'],
    'data': [
        'views/helpdesk_ticket_views.xml',
        'views/website_helpdesk_team_form_inherit.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'incmd_tickets/static/src/js/ticket_form_customization.js',
        ],
    },
    'installable': True,
    'auto_install': False,
}