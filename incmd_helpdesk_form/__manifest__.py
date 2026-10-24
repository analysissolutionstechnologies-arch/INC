# __manifest__.py
{
    'name': 'Personalización Formulario Helpdesk',
    'version': '1.0',
    'category': 'Website/Website',
    'summary': 'Formulario personalizado con validacion de token y productos',
    'description': """
        Extension del formulario de Helpdesk para Agencias BDA.
        Incluye:
        - Seleccion dinamica de agencias y vendedores.
        - Validacion por token de correo electronico.
        - Busqueda y seleccion visual de productos.
    """,
    'depends': [
        'website_helpdesk',  # Modulo base
        'hr',               # Para empleados/departamentos
        'stock',            # Para almacenes
        'product',          # Para productos
        'mail',             
    ],
    'data': [
        'views/helpdesk_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            
            'incmd_helpdesk_form/static/src/js/helpdesk_token.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}