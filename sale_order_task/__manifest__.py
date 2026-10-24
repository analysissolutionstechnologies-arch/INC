{
    'name': 'Sale Order Task',
    'version': '17.0',
    'category': 'Sales',
    'summary': 'Agregar un campo en la orden de venta para mostrar las tareas relacionadas y sus estados.',
    'depends': ['sale', 'project'],
    'data': [
        'views/sale_order_view.xml',
    ],
    'installable': True,
    'application': False,
}
