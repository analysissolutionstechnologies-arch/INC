{
 'name': 'Gestión de Solicitudes INCOMEL', 'version': '19.0.1.0.0',
 'summary': 'Solicitudes internas por área, procesos y supervisión de tiendas',
 'category': 'Services', 'author': 'INCOMEL', 'license': 'LGPL-3',
 'depends': ['base', 'mail', 'web', 'hr'],
 'data': ['security/groups.xml', 'security/ir.model.access.csv', 'security/rules.xml',
          'data/sequence.xml', 'views/config_views.xml', 'views/hr_views.xml', 'views/request_views.xml',
          'wizard/action_views.xml', 'views/menus.xml'],
 'assets': {'web.assets_backend': ['incmd_requests/static/src/scss/requests.scss']},
 'application': True, 'installable': True,
}
