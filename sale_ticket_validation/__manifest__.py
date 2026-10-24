{
    'name': 'Sale Ticket Validation',
    'author': 'Omar Flores - oflores@xetechs.com',
    'website': 'https://www.xetechs.com', 
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'license': 'LGPL-3',
    'summary': 'Sale Ticket Validation Module',
    'description': 'Módulo para validar archivos adjuntos al crear tickets a partir de órdenes de venta',
    'depends': ['sale', 'project'],
    'data': [
        'views/sale_order_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}