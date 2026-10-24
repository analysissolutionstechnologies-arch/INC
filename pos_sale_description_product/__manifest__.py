{
'name': 'Agregar descripcion del producto en las cotizaciones en el pos',
    'summary': 'Agregar descripcion del producto en las cotizaciones en el pos',
    'depends': ['web', 'pos_sale', 'point_of_sale'],
    
    'assets': {
        'point_of_sale._assets_pos': [
          # 'pos_sale_description_product/static/src/js/pricelist_button.js',
            'pos_sale_description_product/static/src/js/payment_screen.js',
            'pos_sale_description_product/static/src/js/pos_store.js',
            'pos_sale_description_product/static/src/js/sale_order_management_screen.js',
            'pos_sale_description_product/static/src/js/sale_order_management_control_panel.js',
            'pos_sale_description_product/static/src/js/custom_sale_order_fetcher.js',
            'pos_sale_description_product/static/src/js/models.js',
            'pos_sale_description_product/static/src/js/sale_order_row.js',
          # 'pos_sale_description_product/static/src/js/set_pricelist_button_patch.js',
            'pos_sale_description_product/static/src/js/custom_set_sale_order_button_patch.js',
            'pos_sale_description_product/static/src/xml/sale_order_list.xml',
            'pos_sale_description_product/static/src/xml/sale_order_row.xml',
            'pos_sale_description_product/static/src/css/custom_pos_message.css',
            'pos_sale_description_product/static/src/css/pos_styles.css',

        ],
    },
    'installable': True,
}
