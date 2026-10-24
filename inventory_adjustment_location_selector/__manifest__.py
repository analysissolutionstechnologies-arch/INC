# -*- coding: utf-8 -*-
{
    'name': 'Inventory Adjustment Location Selector',
    'version': '1.0',
    'summary': 'Permite elegir la ubicación virtual de destino para ajustes (normal / consignación)',
    'description': """
    Añade un campo en el wizard de "Ajuste de inventario" para elegir entre:
     - Ajuste normal (usa la ubicación virtual de ajustes normal)
     - Ajuste consignación (usa la ubicación virtual de ajustes consignación)

    El módulo pasa la elección al contexto y ajusta la location_dest_id al crear movimientos.
    """,
    'author': 'Xetechs, S.A. Enrique Flores ANALISTA DE SOPORTE',
    'category': 'Inventory',
    'depends': ['stock', 'stock_account'],
    'data': [
        'views/stock_inventory_adjustment_name_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}