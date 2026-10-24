{
'name': 'Agregar los almacenes en las cotizaciones en el pos',
    'summary': 'Agregar los almacenes en las cotizaciones en el pos',
    'depends': ['web', 'pos_sale', 'point_of_sale', 'bi_multiwarehouse_for_sales', 'bi_pos_multi_warehouse', 'pos_sale_description_product'],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_sale_warehouses_inh/static/src/js/sale_order_management_screen.js',
            'pos_sale_warehouses_inh/static/src/js/models.js',
            'pos_sale_warehouses_inh/static/src/js/custom_sale_order_fetcher.js',
            'pos_sale_warehouses_inh/static/src/js/sale_order_row.js',
            'pos_sale_warehouses_inh/static/src/xml/sale_order_list.xml',
            'pos_sale_warehouses_inh/static/src/xml/sale_order_row.xml',
            'pos_sale_warehouses_inh/static/src/css/custom_pos_message.css',
            'pos_sale_warehouses_inh/static/src/css/pos_styles.css',
        ],
    },
    'installable': True,
}
