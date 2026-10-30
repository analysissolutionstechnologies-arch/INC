{
    'name': 'Cantidad Disponible en Orden de Venta',
    'version': '17.0',
    'summary': 'Muestra la cantidad disponible del producto en la bodega de la orden de venta',
    'description': 'Añade un campo calculado en las líneas de la orden de venta que muestra la cantidad disponible del producto en la bodega asociada a la orden',
    'author': 'Ximhai',
    'depends': ['sale', 'stock'],
    'data': [
        'views/sale_order_line_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3'
}
