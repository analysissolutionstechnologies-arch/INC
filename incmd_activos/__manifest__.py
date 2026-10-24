{
    'name': 'incmd_activos',
    'summary': 'Gestión de activos fijos, traslados y trazabilidad',
    'description': '''
Gestión de activos fijos de Incomel:
- Alta con autorización por usuario y contraseña de Odoo
- Baja con autorización por usuario y contraseña de Odoo
- Historial de línea de vida
- Traslados con documento PDF
- Documento de responsabilidad
- Exportación Excel XLSX
    ''',
    'version': '17.0.1.16.15',
    'category': 'Inventory/Assets',
    'author': 'Incomel',
    'license': 'LGPL-3',
    'depends': ['base', 'stock', 'hr', 'mail'],
    'data': [
        'security/incmd_activos_security.xml',
        'security/ir.model.access.csv',
        'data/incmd_sequence.xml',
        'report/incmd_reports.xml',
        'views/incmd_activo_views.xml',
        'wizards/incmd_auth_wizard_views.xml',
        'wizards/incmd_traslado_wizard_views.xml',
        'views/incmd_menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'images': ['static/description/icon.png'],
}
