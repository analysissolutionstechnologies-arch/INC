{
    'name': 'Custom Attachment Module',
    'version': '17.0',
    'summary': 'Module for managing and storing attachments using an external API.',
    'description': """
        This module extends ir.attachment to store attachments (images, PDFs, etc.) by 
        converting them to Base64, sending them to an external API, 
        and saving the returned hash in Odoo.
    """,
    'author': 'Ximhai',
    'category': 'Custom',
    'depends': ['base','iframe_widget', 'sale_management', 'project', 'sale_task_attachment', 'mail', 'helpdesk', 'documents'],
    'data': [
            'security/security.xml',
        #  'views/attachment_views.xml',
        #  'views/attachment_menus.xml',
        #  'views/sale_order_view.xml',
        #  'views/project_task_view.xml',
         'views/res_config_settings_view.xml',
        #  'views/documents_document_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'custom_attachment_module/static/src/js/chatter_patch.js',
            'custom_attachment_module/static/src/js/attachment_upload_patch.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'icon': '/custom_attachment_module/static/description/iconxim.png',
    'images': ['static/description/iconxim.png'],
    'license': 'LGPL-3'
}
