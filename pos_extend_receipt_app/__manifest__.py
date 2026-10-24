# -*- coding: utf-8 -*-

{
    "name" : "Advance POS Receipt - QRcode, Barcode on POS Receipt",
    "author": "Edge Technologies",
    "version" : "17.0.1.0",
    "live_test_url":'https://youtu.be/qIKV4TjUg3s',
    "images":["static/description/main_screenshot.png"],
    "price": 12,
    "currency": 'EUR',
    'summary': 'Add customer details on pos receipt invoice number on pos receipt barcode in pos receipt pos barcode receipt pos qrcode receipt pos qr code receipt pos advance receipt pos extended receipt on pos receipt extension point of sale advance receipt barcode pos.',
    "description": """
        This app help to add customer details, invoice number and barcode in pos receipt.
    """,
    "license" : "OPL-1",
    "depends" : ['base','point_of_sale'],
    "data": [
        'views/pos_js.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_extend_receipt_app/static/src/app/model.js',
            'pos_extend_receipt_app/static/src/app/PaymentScreen/payment_screen.js',
            'pos_extend_receipt_app/static/src/app/ReceiptScreen/OrdReceipt.xml',
        ],
    },
    "auto_install": False,
    "installable": True,
    "category" : "Point of Sale",
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
