{
    "name": "Fastapi Incomel",
    "version": "17.0.1.3.1",
    "category": "tools",
    "license": "GPL-3",
    "author": "Setrac",
    "website": "incomel.com",
    "price": 360.00,
    "currency": "USD",
    "depends": ["web", "base", 'sale'],
    "external_dependencies": {
        "python": [ 
            "fastapi",
            "python-multipart",
            "a2wsgi",
            "pyjwt",
            "dotty_dict",
        ]
    },
    "data": [
        "data/ir_config_parameter_data.xml",
        "views/product_template_view.xml",
    ],
    "images": [
        "static/description/banner.jpg",
    ],
    "installable": True,
    "application": False,
}
