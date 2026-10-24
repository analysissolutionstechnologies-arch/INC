{
    'name': 'incmd_pos',
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'description': 'Modulos de punto de venta INCOMEL',
    "author": "Incomel",
    'summary': 'Modulos de punto de venta INCOMEL',
    'depends': ['point_of_sale', 'account', 'web', 'pos_sale'],
    'data': [
        'views/pos_config_view.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            # Que no cambie la lista de precio
            'incmd_pos/static/src/js/pricelist_patch.js',
            # Metodos de pago personalizados
            'incmd_pos/static/src/scss/point_of_sale_customization.css',
            'incmd_pos/static/src/xml/point_of_sale_customization.xml',
            'incmd_pos/static/src/js/point_of_sale_customization.js',
            # El set_pricelist_button_patch restringe los metodos de pago
            'incmd_pos/static/src/js/set_pricelist_button_patch.js',
            # Ocultar boton de reembolso
            'incmd_pos/static/src/js/hide_btn.js',
            # Ocultar ordenes en el pos
            'incmd_pos/static/src/js/ocultarOpcionesPosOrder.js',
        ],
    },
    'installable': True,
    'auto_install': False,
}