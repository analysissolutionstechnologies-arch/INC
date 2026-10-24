{
    'name': 'Widget IFrame URL',
    'version': '17.0.1.0.0',
    'category': 'Tools',
    'summary': 'Widget personalizado para mostrar URLs en iframe',
    'description': """
        Este módulo añade un widget personalizado que permite mostrar
        campos de tipo texto como iframes en las vistas de formulario.
    """,
    'author': 'Tu Nombre',
    'depends': ['web'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'iframe_widget/static/src/js/iframe_url_widget.js',
            'iframe_widget/static/src/xml/iframe_url_widget.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
