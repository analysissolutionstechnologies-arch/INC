# -*- coding: utf-8 -*-

from odoo import api, fields, models


class IncmdCatalogConfig(models.Model):
    _name = 'incmd.catalog.config'
    _description = 'Configuración de Catálogos Públicos'
    _order = 'sequence, id'

    name = fields.Char(string='Nombre', required=True)
    key = fields.Selection(
        selection=[('incomel', 'Incomel'), ('tecnialiado', 'Tecnialiado')],
        string='Catálogo',
        required=True,
    )
    sequence = fields.Integer(string='Secuencia', default=10)
    active = fields.Boolean(string='Activo', default=True)
    page_size = fields.Integer(string='Productos por página', default=12)
    location_ids = fields.Many2many(
        'stock.location',
        'incmd_catalog_config_stock_location_rel',
        'config_id',
        'location_id',
        string='Ubicaciones internas visibles',
        domain=[('usage', '=', 'internal')],
        help='Seleccione las ubicaciones internas que se tomarán en cuenta para mostrar existencias en este catálogo.',
    )

    special_offer_pricelist_id = fields.Many2one(
        'product.pricelist',
        string='Lista de precios - Efectivo',
        help='Lista de precios que se evaluará para calcular el precio de Efectivo usando la lógica nativa de Odoo.',
    )
    credit_pricelist_id = fields.Many2one(
        'product.pricelist',
        string='Lista de precios - Crédito',
        help='Lista de precios que se evaluará primero para calcular el precio de Crédito.',
    )

    special_offer_fallback_field_id = fields.Many2one(
        'ir.model.fields',
        string='Campo respaldo - Efectivo',
        domain="[('model', '=', 'product.template'), ('ttype', 'in', ['float', 'monetary', 'integer'])]",
        help='Campo numérico existente en product.template que se utilizará como respaldo cuando la lista de precios de Efectivo no tenga una regla aplicable. No modifica la ficha del producto.',
    )
    credit_fallback_field_id = fields.Many2one(
        'ir.model.fields',
        string='Campo respaldo - Crédito',
        domain="[('model', '=', 'product.template'), ('ttype', 'in', ['float', 'monetary', 'integer'])]",
        help='Campo numérico existente en product.template que se utilizará como respaldo cuando la lista de precios de Crédito no tenga una regla aplicable. No modifica la ficha del producto.',
    )


    _sql_constraints = [
        ('key_unique', 'unique(key)', 'Ya existe una configuración para este catálogo.'),
    ]

    @api.constrains('page_size')
    def _check_page_size(self):
        for record in self:
            if record.page_size < 1:
                record.page_size = 12
            elif record.page_size > 60:
                record.page_size = 60

    def init(self):
        """Crea las configuraciones base de forma idempotente.

        Antes existían registros XML en data/catalog_config_data.xml. En bases donde
        el registro ya fue creado manualmente o por una versión previa, Odoo podía
        intentar crearlo otra vez y fallaba por unique(key). Con este método usamos
        ON CONFLICT DO NOTHING para que instalar/actualizar sea seguro.
        """
        self.env.cr.execute("""
            INSERT INTO incmd_catalog_config (name, key, sequence, page_size, active, create_uid, create_date, write_uid, write_date)
            VALUES
                ('Incomel', 'incomel', 10, 12, true, 1, NOW(), 1, NOW()),
                ('Tecnialiado', 'tecnialiado', 20, 12, true, 1, NOW(), 1, NOW())
            ON CONFLICT (key) DO NOTHING
        """)
