# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
from datetime import date


class IncmdActivo(models.Model):
    _name = 'incmd.activo'
    _description = 'Activo Fijo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    code = fields.Char(
        string='Código / Correlativo',
        readonly=True,
        copy=False,
        tracking=True,
        default=lambda self: _('Pendiente')
    )
    name = fields.Char(
        string='Nombre / Descripción',
        compute='_compute_name',
        store=True,
        readonly=True,
        tracking=True
    )
    product_id = fields.Many2one(
        'product.template',
        string='Código de Barras',
        copy=False,
        tracking=True,
        help='Buscar por nombre o código de barras del producto',
    )
    barcode = fields.Char(
        string='Barcode',
        related='product_id.barcode',
        store=True,
        readonly=True,
    )
    generic = fields.Char(string='Genérico')
    brand = fields.Char(string='Marca')
    model = fields.Char(string='Modelo')
    serie = fields.Char(string='Serie')

    responsible_employee_id = fields.Many2one(
        'hr.employee',
        string='Persona Responsable',
        tracking=True
    )
    location_id = fields.Many2one(
        'stock.warehouse',
        string='Ubicación Actual',
        required=True,
        tracking=True
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Departamento',
        tracking=True
    )
    requires_department = fields.Boolean(
        string='Requiere Departamento',
        compute='_compute_requires_department',
        store=False
    )

    nit_proveedor = fields.Char(
        string='NIT Proveedor',
        tracking=True,
        help='Ingrese el NIT para buscar el proveedor y filtrar sus facturas.',
    )
    supplier_partner_id = fields.Many2one(
        'res.partner',
        string='Proveedor',
        tracking=True,
        readonly=True,
    )
    purchase_invoice_id = fields.Many2one(
        'account.move',
        string='Factura de compra',
        domain="[('move_type', 'in', ('in_invoice', 'in_refund')), ('state', '=', 'posted'), ('partner_id', '=', supplier_partner_id)]",
        tracking=True,
        help='Se habilita al encontrar el proveedor por NIT.',
    )
    supplier_name = fields.Char(string='Nombre de proveedor')
    original_value = fields.Monetary(string='Valor original')
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id.id
    )
    purchase_date = fields.Date(string='Fecha de compra')
    depreciation_rate = fields.Float(string='Depreciación (%)', digits=(5, 2))


    state = fields.Selection([
        ('draft', 'Borrador'),
        ('assigned', 'Asignado'),
        ('transit', 'En Tránsito'),
        ('archived', 'Baja'),
    ], string='Estado', default='draft', required=True, tracking=True)

    history_ids = fields.One2many(
        'incmd.activo.history',
        'activo_id',
        string='Historial de Línea de Vida',
        readonly=True
    )

    active = fields.Boolean(default=True)


    @api.depends('code', 'generic')
    def _compute_name(self):
        for rec in self:
            code = rec.code or ''
            generic = rec.generic or ''
            if code and generic:
                rec.name = '%s — %s' % (code, generic)
            elif code:
                rec.name = code
            elif generic:
                rec.name = generic
            else:
                rec.name = ''

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            self.generic = False
            self.brand = False
            self.model = False
            return
        self.generic = self.product_id.x_studio_generico or False
        self.brand = self.product_id.x_studio_marca or False
        self.model = self.product_id.x_studio_modelo or False

    @api.onchange('nit_proveedor')
    def _onchange_nit_proveedor(self):
        """Busca en account.move el partner con el NIT ingresado y llena supplier_partner_id."""
        self.supplier_partner_id = False
        self.purchase_invoice_id = False
        if not self.nit_proveedor:
            return
        # Buscar en facturas de proveedor un partner con ese VAT
        move = self.env['account.move'].search([
            ('move_type', 'in', ('in_invoice', 'in_refund')),
            ('state', '=', 'posted'),
            ('partner_id.vat', '=', self.nit_proveedor.strip()),
        ], limit=1)
        if move:
            self.supplier_partner_id = move.partner_id
        else:
            return {
                'warning': {
                    'title': _('NIT no encontrado'),
                    'message': _('No se encontró ningún proveedor con NIT "%s" en las facturas registradas.') % self.nit_proveedor,
                }
            }

    @api.onchange('supplier_partner_id')
    def _onchange_supplier_partner_id(self):
        """Al cambiar el proveedor, limpiar la factura seleccionada."""
        self.purchase_invoice_id = False

    @api.depends('location_id')
    def _compute_requires_department(self):
        for rec in self:
            rec.requires_department = rec._is_matriz_location(rec.location_id)

    def _is_matriz_location(self, location):
        if not location:
            return False
        name = (location.name or '').lower()
        return 'matriz' in name

    @api.constrains('location_id', 'department_id')
    def _check_department_required_for_matriz(self):
        for rec in self:
            if rec._is_matriz_location(rec.location_id) and not rec.department_id:
                raise ValidationError(_('El Departamento es obligatorio cuando la ubicación seleccionada corresponde a Matriz.'))

    def _generate_code(self):
        today = date.today()
        seq = self.env['ir.sequence'].next_by_code('incmd.activo') or '00001'
        return 'AF-INC-%s-%s-%s-%s' % (
            today.strftime('%Y'),
            today.strftime('%m'),
            today.strftime('%d'),
            seq,
        )

    def _ensure_code(self):
        for rec in self:
            if not rec.code or rec.code == _('Pendiente'):
                rec.code = rec._generate_code()


    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.user.has_group('incmd_activos.group_incmd_activos_manager'):
            raise AccessError(_('Solo los administradores de activos pueden crear activos fijos.'))
        records = super().create(vals_list)
        records._ensure_code()
        return records

    def write(self, vals):
        # Capturar valores anteriores antes de escribir
        tracked_fields = {'state', 'location_id'}
        if tracked_fields & set(vals.keys()):
            for rec in self:
                old_state = rec.state
                old_location = rec.location_id

                result = super(IncmdActivo, rec).write(vals)

                new_state = rec.state
                new_location = rec.location_id

                state_changed = old_state != new_state
                location_changed = old_location != new_location

                if state_changed or location_changed:
                    # Determinar tipo de evento
                    if state_changed and new_state == 'assigned' and old_state == 'draft':
                        event_type = 'alta'
                    elif state_changed and new_state == 'archived':
                        event_type = 'baja'
                    elif location_changed:
                        event_type = 'traslado'
                    else:
                        event_type = 'cambio_estado'

                    rec._create_history(
                        event_type=event_type,
                        origin_location=old_location if location_changed else False,
                        destination_location=new_location if location_changed else False,
                    )
            return result
        return super().write(vals)

    def _create_history(self, event_type, origin_location=False, destination_location=False):
        self.ensure_one()
        self.env['incmd.activo.history'].create({
            'activo_id': self.id,
            'date': fields.Datetime.now(),
            'origin_location_id': origin_location.id if origin_location else False,
            'destination_location_id': destination_location.id if destination_location else False,
            'department_id': self.department_id.id if self.department_id else False,
            'responsible_employee_id': self.responsible_employee_id.id if self.responsible_employee_id else False,
            'event_type': event_type,
            'executed_by_id': self.env.context.get('authorized_user_id') or self.env.user.id,
            'observation': self.env.context.get('baja_observation') if event_type == 'baja' else False,
        })

    def action_open_activate_wizard(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Solo se pueden activar activos en estado Borrador.'))
        return {
            'name': _('Autorizar Alta de Activo'),
            'type': 'ir.actions.act_window',
            'res_model': 'incmd.activo.auth.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_activo_id': self.id,
                'default_action_type': 'activate',
            },
        }

    def action_open_archive_wizard(self):
        self.ensure_one()
        if self.state == 'archived':
            raise UserError(_('El activo ya se encuentra dado de baja.'))
        return {
            'name': _('Autorizar Baja de Activo'),
            'type': 'ir.actions.act_window',
            'res_model': 'incmd.activo.auth.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_activo_id': self.id,
                'default_action_type': 'archive',
            },
        }


    def _check_admin_activos(self):
        if not self.env.user.has_group('incmd_activos.group_incmd_activos_manager'):
            raise AccessError(_('Solo los administradores de activos pueden ejecutar esta acción.'))

    def action_open_traslado_wizard(self):
        self.ensure_one()
        self._check_admin_activos()
        if self.state not in ('assigned', 'transit'):
            raise UserError(_('Solo se pueden trasladar activos asignados o en tránsito.'))
        return {
            'name': _('Trasladar Activo'),
            'type': 'ir.actions.act_window',
            'res_model': 'incmd.activo.traslado.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_activo_id': self.id},
        }

    def action_print_responsabilidad(self):
        self.ensure_one()
        self._check_admin_activos()
        return self.env.ref('incmd_activos.action_report_incmd_responsabilidad').report_action(self)

    def action_print_history(self):
        self.ensure_one()
        self._check_admin_activos()
        return self.env.ref('incmd_activos.action_report_incmd_linea_vida').report_action(self)

    def action_export_xlsx(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/incmd_activos/export_xlsx',
            'target': 'self',
        }
