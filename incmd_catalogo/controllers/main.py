# -*- coding: utf-8 -*-

import logging
import urllib.parse
from odoo import fields, http
from odoo.http import request
from odoo.tools.image import image_data_uri
from odoo.tools.float_utils import float_compare

_logger = logging.getLogger(__name__)

CATALOGS = {
    'incomel': {
        'name': 'Incomel',
        'base_path': '/incomel',
        'product_field': 'x_mostrar_en_incomel',
        'logo': '/incmd_catalogo/static/img/logo_japon.png',
        'page_size_param': 'incmd_catalogo.incomel.page_size',
        'email': 'ventas@incomel.com.gt',
        'title': 'Catálogo de Electrodomésticos',
        'stock_label': 'Almacenes Japón',
        'phone_param': 'incmd_catalogo.incomel.phone',
        'phone_default': '502 2420-9300',
        'whatsapp_param': 'incmd_catalogo.incomel.whatsapp',
        'whatsapp_default': '50259518116',
    },
    'tecnialiado': {
        'name': 'Tecnialiado',
        'base_path': '/tecnialiado',
        'product_field': 'x_mostrar_en_tecnialiado',
        'logo': '/incmd_catalogo/static/img/logo_tecnialiado_temp.svg',
        'page_size_param': 'incmd_catalogo.tecnialiado.page_size',
        'email': 'ventas@incomel.com.gt',
        'title': 'Catálogo Tecnialiado',
        'stock_label': 'Tecnialiado',
        'phone_param': 'incmd_catalogo.tecnialiado.phone',
        'phone_default': '502 2420-9300',
        'whatsapp_param': 'incmd_catalogo.tecnialiado.whatsapp',
        'whatsapp_default': '50259518116',
    },
}


def _get_catalog(key):
    return CATALOGS.get(key) or CATALOGS['incomel']


def _get_currency(producto):
    currency = producto.currency_id or request.env.company.currency_id
    return currency.symbol or '', currency.position or 'before'


def _get_catalog_config(catalog_key):
    Config = request.env['incmd.catalog.config'].sudo()
    config = Config.search([('key', '=', catalog_key), ('active', '=', True)], limit=1)
    if not config:
        config = Config.search([('key', '=', catalog_key)], limit=1)
    return config


def _get_catalog_locations(catalog_key):
    """Resuelve las ubicaciones de inventario del catálogo sin modificar datos.

    Prioridad:
      1) Ubicaciones seleccionadas en ``incmd.catalog.config.location_ids``.
      2) Compatibilidad con el parámetro histórico
         ``incmd_catalogo.<catalogo>.location_keywords``.

    El parámetro histórico admite entradas como::

        siner/existencias:Sinergias,centr/existencias:Bodega Central

    La parte anterior a ``:`` es el texto usado para localizar
    ``stock.location.complete_name``. La parte posterior es solo una etiqueta.
    """
    StockLocation = request.env['stock.location'].sudo()
    config = _get_catalog_config(catalog_key)

    locations = StockLocation.browse()
    if config and config.location_ids:
        locations |= config.location_ids.sudo()

    # Compatibilidad con configuraciones de versiones anteriores. Se utiliza
    # como respaldo y también se combina con el Many2many para evitar que una
    # ubicación válida deje de contar después de una actualización del módulo.
    params = request.env['ir.config_parameter'].sudo()
    raw_keywords = params.get_param(
        'incmd_catalogo.%s.location_keywords' % catalog_key,
        '',
    ) or ''

    for entry in raw_keywords.split(','):
        entry = (entry or '').strip()
        if not entry:
            continue
        selector = entry.split(':', 1)[0].strip()
        if not selector:
            continue

        matched = StockLocation.search([
            ('usage', '=', 'internal'),
            ('complete_name', 'ilike', selector),
        ])
        locations |= matched

    # Solo ubicaciones internas. No se hace write/create/unlink.
    locations = locations.filtered(lambda loc: loc.usage == 'internal')
    return locations


def _get_catalog_location_ids(catalog_key):
    """Compatibilidad interna para llamadas existentes."""
    return _get_catalog_locations(catalog_key).ids


def _get_catalog_location_aliases(catalog_key):
    """Devuelve aliases amigables configurados para ubicaciones.

    Lee el parámetro histórico ``incmd_catalogo.<catalogo>.location_keywords``
    con formato ``selector:Etiqueta`` y devuelve una lista de pares
    ``(selector_en_minusculas, etiqueta_amigable)``.
    """
    aliases = []
    params = request.env['ir.config_parameter'].sudo()
    raw_keywords = params.get_param(
        'incmd_catalogo.%s.location_keywords' % catalog_key,
        '',
    ) or ''

    for entry in raw_keywords.split(','):
        entry = (entry or '').strip()
        if not entry:
            continue
        parts = entry.split(':', 1)
        selector = (parts[0] or '').strip().lower()
        label = (parts[1] or '').strip() if len(parts) > 1 else ''
        if selector:
            aliases.append((selector, label))
    return aliases


def _normalize_stock_location_label(label):
    """Normaliza nombres técnicos de ubicaciones a textos amigables."""
    raw = (label or '').strip()
    low = raw.lower()

    if 'siner' in low:
        return 'Bodega Sinergias'
    if 'centr' in low:
        return 'Bodega Central'

    # Si por configuración histórica viene solo el nombre corto, también se normaliza.
    if low == 'sinergias':
        return 'Bodega Sinergias'
    return raw


def _get_stock_location_label(location, catalog_key):
    """Devuelve la etiqueta visible de la ubicación para el catálogo."""
    location_full_name = (location.complete_name or location.display_name or location.name or '').strip()
    location_full_name_low = location_full_name.lower()

    for selector, alias in _get_catalog_location_aliases(catalog_key):
        if selector and selector in location_full_name_low:
            return _normalize_stock_location_label(alias or location_full_name)

    return _normalize_stock_location_label(location_full_name)


def _get_pricelist_rule_price(producto, pricelist, quantity=1.0):
    """Devuelve (precio, moneda, regla_id) con la lógica nativa de Odoo.

    Orden solicitado para el catálogo:
      1) Evaluar primero la plantilla contra la lista de precios.
      2) Si no existe una regla aplicable para la plantilla, evaluar variantes.
      3) Si tampoco existe regla aplicable en variantes, devolver sin regla para
         que el llamador utilice el precio de la ficha (list_price).

    ``_get_product_price_rule`` conserva la lógica nativa de Odoo para vigencia,
    categorías, fórmulas, descuentos y listas encadenadas/base_pricelist_id.
    """
    if not pricelist:
        return None, None, False

    date = fields.Datetime.now()

    def _native_price(product):
        try:
            price, rule_id = pricelist._get_product_price_rule(
                product,
                quantity=quantity,
                currency=pricelist.currency_id,
                uom=product.uom_id,
                date=date,
            )
            if rule_id and price is not None:
                return float(price), rule_id
        except Exception as e:
            _logger.warning(
                'INCMD Pricelist error (%s / %s): %s',
                pricelist.display_name, product.display_name, e,
            )
        return None, False

    # 1. Primero la ficha/plantilla dentro de la lista de precios.
    price, rule_id = _native_price(producto)
    if rule_id and price is not None and price > 0:
        return price, pricelist.currency_id, rule_id

    # 2. Si la plantilla no encontró regla, validar las variantes.
    variants = producto.product_variant_ids
    if variants:
        variant_results = []
        for variant in variants.sorted('id'):
            price, rule_id = _native_price(variant)
            if rule_id and price is not None and price > 0:
                variant_results.append((price, rule_id))

        if variant_results:
            # El catálogo muestra product.template; cuando hay más de una variante
            # con precio válido se publica el menor precio positivo encontrado.
            price, rule_id = min(variant_results, key=lambda item: item[0])
            return price, pricelist.currency_id, rule_id

    return None, None, False


def _find_catalog_pricelist(exact_name, configured_pricelist=False):
    """Busca primero la lista requerida por nombre exacto y luego usa configuración.

    Esto evita depender de que el Many2one haya quedado configurado después de una
    actualización. No crea ni modifica listas de precios.
    """
    Pricelist = request.env['product.pricelist'].sudo()
    company = request.env.company

    # Preferir una lista de la compañía actual.
    pricelist = Pricelist.search([
        ('name', '=ilike', exact_name),
        ('company_id', '=', company.id),
    ], limit=1)
    if not pricelist:
        # Luego una lista global con el mismo nombre.
        pricelist = Pricelist.search([
            ('name', '=ilike', exact_name),
            ('company_id', '=', False),
        ], limit=1)
    if not pricelist:
        # Compatibilidad por si la base no usa company_id como se espera.
        pricelist = Pricelist.search([('name', '=ilike', exact_name)], limit=1)

    return pricelist or configured_pricelist


def _get_catalog_prices(producto, catalog_key='incomel', quantity=1.0):
    """Calcula Efectivo y Crédito sin modificar la ficha del producto.

    Efectivo:
      - Lista ``PRECIO OFERTA ESPECIAL``.
    Crédito:
      - Lista ``CRÉDITO``.

    Para cada precio:
      1) se usa la lista con el motor nativo de Odoo;
      2) si no hay regla en plantilla, se revisan variantes;
      3) si no hay regla tampoco en variantes, se usa ``product.template.list_price``.

    Si Efectivo y Crédito son iguales, se oculta Efectivo y se muestra únicamente
    Crédito, según la regla comercial solicitada.
    """
    config = _get_catalog_config(catalog_key)
    product_currency = producto.currency_id or request.env.company.currency_id

    configured_cash = config.special_offer_pricelist_id if config else False
    configured_credit = config.credit_pricelist_id if config else False

    cash_pricelist = _find_catalog_pricelist('PRECIO OFERTA ESPECIAL', configured_cash)
    credit_pricelist = _find_catalog_pricelist('CRÉDITO', configured_credit)

    cash_price, cash_currency, cash_rule_id = _get_pricelist_rule_price(
        producto, cash_pricelist, quantity=quantity,
    )
    credit_price, credit_currency, credit_rule_id = _get_pricelist_rule_price(
        producto, credit_pricelist, quantity=quantity,
    )

    # Última caída: precio de la ficha del producto. Solo lectura.
    if not cash_rule_id:
        cash_price = float(producto.list_price or 0.0)
        cash_currency = product_currency
    if not credit_rule_id:
        credit_price = float(producto.list_price or 0.0)
        credit_currency = product_currency

    cash_price = float(cash_price or 0.0)
    credit_price = float(credit_price or 0.0)

    same_price = False
    if (
        cash_price > 0 and credit_price > 0
        and cash_currency and credit_currency
        and cash_currency == credit_currency
    ):
        same_price = float_compare(
            cash_price,
            credit_price,
            precision_rounding=cash_currency.rounding,
        ) == 0

    return {
        # ``special_*`` se conserva para no romper las plantillas existentes.
        # Funcionalmente ahora representa Efectivo / PRECIO OFERTA ESPECIAL.
        'cash_price': cash_price,
        'cash_currency_symbol': cash_currency.symbol if cash_currency else '',
        'cash_currency_position': cash_currency.position if cash_currency else 'before',
        'cash_price_formatted': format(cash_price, ',.2f'),
        'special_price': cash_price,
        'special_currency_symbol': cash_currency.symbol if cash_currency else '',
        'special_currency_position': cash_currency.position if cash_currency else 'before',
        'special_price_formatted': format(cash_price, ',.2f'),
        'special_from_pricelist': bool(cash_rule_id),
        'credit_price': credit_price,
        'credit_currency_symbol': credit_currency.symbol if credit_currency else '',
        'credit_currency_position': credit_currency.position if credit_currency else 'before',
        'credit_price_formatted': format(credit_price, ',.2f'),
        'credit_from_pricelist': bool(credit_rule_id),
        # Regla solicitada: si son iguales, mostrar únicamente Crédito.
        'hide_cash_price': False,
        'hide_credit_price': same_price,
    }


def _get_stock(producto, catalog_key='incomel'):
    """Lee la existencia física desde stock.quant sin modificar inventario.

    Solo toma ``stock.quant.quantity`` de las ubicaciones configuradas para el
    catálogo y de sus sububicaciones internas. No hace write/unlink/create,
    no reserva producto y no modifica ningún campo de product.template.
    """
    stock_detail = []
    try:
        StockQuant = request.env['stock.quant'].sudo()
        StockLocation = request.env['stock.location'].sudo()

        variant_ids = producto.product_variant_ids.ids
        if not variant_ids:
            return [], 0

        configured_locations = _get_catalog_locations(catalog_key)
        configured_location_ids = configured_locations.ids
        if not configured_location_ids:
            _logger.warning(
                'INCMD Stock: catálogo %s sin ubicaciones resueltas para producto template=%s variantes=%s. '
                'Revise location_ids o incmd_catalogo.%s.location_keywords',
                catalog_key, producto.id, variant_ids, catalog_key,
            )
            return [], 0

        # Resolver las ubicaciones configuradas + todas sus sububicaciones.
        # Esta consulta es solamente de lectura. ``child_of`` incluye también
        # la propia ubicación configurada.
        allowed_locations = StockLocation.search([
            ('id', 'child_of', configured_location_ids),
            ('usage', '=', 'internal'),
        ])
        allowed_location_ids = allowed_locations.ids

        if not allowed_location_ids:
            return [], 0

        # Leer la cantidad física directamente de stock.quant. Se incluyen
        # positivos y negativos y luego se suma el saldo real por ubicación.
        quants = StockQuant.search([
            ('product_id', 'in', variant_ids),
            ('location_id', 'in', allowed_location_ids),
        ])

        by_location = {}
        for quant in quants:
            qty = float(quant.quantity or 0.0)
            location = quant.location_id
            label = _get_stock_location_label(location, catalog_key)
            by_location[label] = by_location.get(label, 0.0) + qty

        # Mostrar en el detalle únicamente ubicaciones con saldo físico positivo.
        for label, qty in sorted(by_location.items()):
            if qty <= 0:
                continue
            qty_display = int(qty) if float(qty).is_integer() else round(qty, 2)
            stock_detail.append({'location': label, 'qty': qty_display})

        if not stock_detail:
            _logger.info(
                'INCMD Stock: sin existencia positiva template=%s variantes=%s catálogo=%s ubicaciones=%s',
                producto.id,
                variant_ids,
                catalog_key,
                [(loc.id, loc.complete_name or loc.display_name or loc.name) for loc in allowed_locations],
            )

    except Exception as e:
        _logger.error(
            'INCMD Stock error producto=%s catálogo=%s: %s',
            producto.id, catalog_key, e, exc_info=True,
        )

    qty_total = sum(float(s['qty']) for s in stock_detail)
    qty_total = int(qty_total) if float(qty_total).is_integer() else round(qty_total, 2)
    return stock_detail, qty_total


def _build_product_dict(producto, catalog_key='incomel'):
    imagen_512 = producto.image_512 or producto.image_1920
    imagenes_extra = []
    for variant in producto.product_variant_ids[:4]:
        img = variant.image_512 or variant.image_1920
        if img:
            imagenes_extra.append(image_data_uri(img))

    currency_symbol, currency_position = _get_currency(producto)
    specs = []
    for line in producto.attribute_line_ids:
        vals = ', '.join(line.value_ids.mapped('name'))
        specs.append({'attr': line.attribute_id.name, 'val': vals})

    stock_detail, qty_total = _get_stock(producto, catalog_key)
    catalog = _get_catalog(catalog_key)
    params = request.env['ir.config_parameter'].sudo()
    whatsapp_number = params.get_param(
        catalog.get('whatsapp_param'),
        catalog.get('whatsapp_default', ''),
    ) or ''
    whatsapp_number = ''.join(ch for ch in whatsapp_number if ch.isdigit())
    catalog_prices = _get_catalog_prices(producto, catalog_key)

    return {
        'id': producto.id,
        'name': producto.name or '',
        'sku': producto.default_code or '',
        'description_sale': producto.description_sale or '',
        'description': producto.description or '',
        'x_disponible': qty_total > 0,
        'categoria': producto.categ_id.name if producto.categ_id else '',
        'categoria_completa': producto.categ_id.complete_name if producto.categ_id else '',
        'image_src': image_data_uri(imagen_512) if imagen_512 else '/web/static/img/placeholder.png',
        'imagenes_extra': imagenes_extra,
        'list_price': producto.list_price,
        'currency_symbol': currency_symbol,
        'currency_position': currency_position,
        **catalog_prices,
        'specs': specs,
        'stock_detail': stock_detail,
        'qty_total': qty_total,
        'qty_ubicaciones': len(stock_detail),
        'whatsapp_number': whatsapp_number,
    }


def _is_catalog_enabled(catalog_key):
    """Retorna True cuando el catálogo está habilitado por parámetro de sistema."""
    value = request.env['ir.config_parameter'].sudo().get_param(
        'incmd_catalogo.%s.enabled' % catalog_key,
        'True',
    )
    return str(value).strip().lower() in ('1', 'true', 'yes', 'y', 'on', 'si', 'sí')


def _ensure_catalog_enabled(catalog_key):
    """Devuelve una respuesta 404 si el catálogo está deshabilitado."""
    if not _is_catalog_enabled(catalog_key):
        return request.not_found()
    return None


class IncomelCatalogoController(http.Controller):
    DEFAULT_PAGE_SIZE = 12

    def _get_page_size(self, catalog_key):
        config = _get_catalog_config(catalog_key)
        try:
            page_size = int(config.page_size or self.DEFAULT_PAGE_SIZE) if config else self.DEFAULT_PAGE_SIZE
        except Exception:
            page_size = self.DEFAULT_PAGE_SIZE
        if page_size < 1:
            page_size = self.DEFAULT_PAGE_SIZE
        if page_size > 60:
            page_size = 60
        return page_size

    def _catalog_context(self, catalog_key):
        catalog = dict(_get_catalog(catalog_key))
        params = request.env['ir.config_parameter'].sudo()
        phone = params.get_param(catalog['phone_param'], catalog.get('phone_default', '')) or ''
        catalog['phone'] = phone.strip()
        catalog['phone_href'] = ''.join(ch for ch in catalog['phone'] if ch.isdigit() or ch == '+')
        catalog['key'] = catalog_key
        catalog['catalog_url'] = catalog['base_path'] + '/catalogo'
        catalog['about_url'] = catalog['base_path'] + '/nosotros'
        return catalog

    def _catalogo(self, catalog_key, categoria_id=None, q=None, disponible=None, page=1, **kwargs):
        blocked = _ensure_catalog_enabled(catalog_key)
        if blocked is not None:
            return blocked

        catalog = self._catalog_context(catalog_key)
        ProductTemplate = request.env['product.template'].sudo()
        ProductCategory = request.env['product.category'].sudo()

        if catalog_key == 'incomel':
            # Compatibilidad: productos marcados en versiones anteriores con x_mostrar_en_catalogo
            # también se muestran en Incomel, para no dejar el catálogo vacío al actualizar.
            base_domain = [('active', '=', True), '|', ('x_mostrar_en_incomel', '=', True), ('x_mostrar_en_catalogo', '=', True)]
        else:
            base_domain = [('active', '=', True), (catalog['product_field'], '=', True)]

        grouped_categories = ProductTemplate.read_group(
            base_domain + [('categ_id', '!=', False)], fields=['categ_id'], groupby=['categ_id'], lazy=False,
        )
        category_ids = [item['categ_id'][0] for item in grouped_categories if item.get('categ_id')]
        categorias = ProductCategory.browse(category_ids).exists().sorted(lambda c: c.complete_name or c.name)

        selected_category = False
        domain = list(base_domain)
        if categoria_id:
            try:
                categoria_id_int = int(categoria_id)
                selected_category = ProductCategory.browse(categoria_id_int).exists()
                if selected_category:
                    domain.append(('categ_id', 'child_of', selected_category.id))
            except (TypeError, ValueError):
                selected_category = False

        search_term = (q or '').strip()
        if search_term:
            domain += ['|', ('name', 'ilike', search_term), ('description_sale', 'ilike', search_term)]

        try:
            page = max(1, int(page))
        except (TypeError, ValueError):
            page = 1

        # La disponibilidad pública depende únicamente de la existencia física
        # leída desde stock.quant en las ubicaciones configuradas.
        candidate_products = ProductTemplate.search(domain, order='name asc')
        product_rows = []
        for p in candidate_products:
            _stock_detail, qty_total = _get_stock(p, catalog_key)

            # REGLA PRINCIPAL DEL CATÁLOGO:
            # si no existe stock positivo en ninguna de las ubicaciones
            # configuradas (por ejemplo Central + Sinergia), el producto NO se
            # publica, independientemente de filtros visuales.
            if qty_total <= 0:
                continue

            # La disponibilidad se determina EXCLUSIVAMENTE por stock.quant.
            # No se consulta ni modifica x_disponible para decidir la publicación.
            is_available = True

            if disponible == '0':
                # Los productos sin existencia no se publican en el catálogo.
                continue

            product_rows.append((p, is_available, qty_total))

        total = len(product_rows)
        page_size = self._get_page_size(catalog_key)
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = min(page, total_pages)
        offset = (page - 1) * page_size
        product_rows = product_rows[offset:offset + page_size]

        productos_catalogo = []
        for p, is_available, qty_total in product_rows:
            imagen = p.image_512 or p.image_1920
            currency_symbol, currency_position = _get_currency(p)
            catalog_prices = _get_catalog_prices(p, catalog_key)
            productos_catalogo.append({
                'id': p.id,
                'name': p.name or '',
                'x_disponible': is_available,
                'qty_total': qty_total,
                'categoria': p.categ_id.name if p.categ_id else '',
                'image_src': image_data_uri(imagen) if imagen else '/web/static/img/placeholder.png',
                'list_price': p.list_price,
                'currency_symbol': currency_symbol,
                'currency_position': currency_position,
                **catalog_prices,
            })

        params = {}
        if categoria_id:
            params['categoria_id'] = categoria_id
        if search_term:
            params['q'] = search_term
        if disponible in ('1', '0'):
            params['disponible'] = disponible
        base_url = catalog['catalog_url'] + '?' + urllib.parse.urlencode(params) + ('&' if params else '')

        return request.render('incmd_catalogo.catalogo_home_template', {
            'catalog': catalog,
            'productos': productos_catalogo,
            'categorias': categorias,
            'selected_category': selected_category,
            'q': search_term,
            'disponible': disponible if disponible in ('1', '0') else '',
            'page': page,
            'total_pages': total_pages,
            'total': total,
            'base_url': base_url,
            'page_size': page_size,
        })

    @http.route(['/incomel', '/incomel/catalogo'], type='http', auth='public', website=True, sitemap=True)
    def incomel_catalogo(self, **kwargs):
        return self._catalogo('incomel', **kwargs)

    @http.route(['/tecnialiado', '/tecnialiado/catalogo'], type='http', auth='public', website=True, sitemap=True)
    def tecnialiado_catalogo(self, **kwargs):
        return self._catalogo('tecnialiado', **kwargs)

    def _producto(self, catalog_key, producto_id, **kwargs):
        blocked = _ensure_catalog_enabled(catalog_key)
        if blocked is not None:
            return blocked

        catalog = self._catalog_context(catalog_key)
        ProductTemplate = request.env['product.template'].sudo()
        producto = ProductTemplate.browse(producto_id).exists()
        if not producto:
            return request.redirect(catalog['catalog_url'])

        visible_flag = bool(getattr(producto, catalog['product_field']))
        if catalog_key == 'incomel':
            visible_flag = visible_flag or bool(producto.x_mostrar_en_catalogo)
        if not visible_flag:
            return request.redirect(catalog['catalog_url'])

        # Evita que un producto sin existencia se vea entrando directamente por URL.
        _stock_detail, qty_total = _get_stock(producto, catalog_key)
        if qty_total <= 0:
            return request.redirect(catalog['catalog_url'])

        return request.render('incmd_catalogo.catalogo_producto_template', {
            'catalog': catalog,
            'producto': _build_product_dict(producto, catalog_key),
            'quote_plus': urllib.parse.quote_plus,
        })

    @http.route(['/incomel/producto/<int:producto_id>'], type='http', auth='public', website=True, sitemap=False)
    def incomel_producto(self, producto_id, **kwargs):
        return self._producto('incomel', producto_id, **kwargs)

    @http.route(['/tecnialiado/producto/<int:producto_id>'], type='http', auth='public', website=True, sitemap=False)
    def tecnialiado_producto(self, producto_id, **kwargs):
        return self._producto('tecnialiado', producto_id, **kwargs)

    def _nosotros(self, catalog_key, **kwargs):
        blocked = _ensure_catalog_enabled(catalog_key)
        if blocked is not None:
            return blocked

        return request.not_found()

    @http.route(['/incomel/nosotros'], type='http', auth='public', website=True, sitemap=False)
    def incomel_nosotros(self, **kwargs):
        return self._nosotros('incomel', **kwargs)

    @http.route(['/tecnialiado/nosotros'], type='http', auth='public', website=True, sitemap=False)
    def tecnialiado_nosotros(self, **kwargs):
        return self._nosotros('tecnialiado', **kwargs)
