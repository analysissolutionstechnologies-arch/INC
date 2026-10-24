/** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
    
   getReceiptHeaderData(order) {
        debugger
        const result = super.getReceiptHeaderData(...arguments);
        result.is_order_number = this.config.order_number;
        result.is_customer_details = this.config.customer_details;
        result.is_customer_name = this.config.customer_name;
        result.customer_address = this.config.customer_address;
        result.customer_mobile = this.config.customer_mobile;
        result.customer_phone = this.config.customer_phone;
        result.customer_email = this.config.customer_email;
        result.customer_vat = this.config.customer_vat;
        result.invoice_number = this.config.invoice_number;
        result.order_barcode = this.config.order_barcode;
        result.barcode_selection = this.config.barcode_selection;
        // Validar si order es undefined y asignar el valor de this.orders[0]
        if (!order && this.orders && this.orders.length > 0) {
            order = this.orders[0];
        }

        result.order = order;
            result.order= order;
            var barcode = '/report/barcode/Code128/' + order.uid;
            result.barcode= barcode;
            var qrcode = '/report/barcode/QR/' + order.uid;
            result.qrcode = qrcode;
            return result;
        }
});



patch(Order.prototype, {
    setup() {
        super.setup(...arguments);
        this.invoice_number = this.invoice_number || false;
        this.fel_serie = this.fel_serie || false;
        this.fel_numero = this.fel_numero || false;
        this.fel_numero_autorizacion = this.fel_numero_autorizacion || false;
        this.plazo = this.plazo || false;
        this.tipo_flujo = this.tipo_flujo || false;
        this.cuota_autorizada = this.cuota_autorizada || false;
        this.documento_personal_identificacion = this.documento_personal_identificacion || false;
        this.cliente_vat = this.cliente_vat || false;
        this.cliente_dpi = this.cliente_dpi || false;
    },
    set_invoice_number(invoice_number){
        this.invoice_number = invoice_number;
    },
    get_invoice_number(){
        return this.invoice_number;
    },
    set_fel_serie(fel_serie) {
        this.fel_serie = fel_serie;
    },
    get_fel_serie() {
        return this.fel_serie;
    },
    set_fel_numero(fel_numero) {
        this.fel_numero = fel_numero;
    },
    get_fel_numero() {
        return this.fel_numero;
    },
    set_fel_numero_autorizacion(fel_numero_autorizacion) {
        this.fel_numero_autorizacion = fel_numero_autorizacion;
    },
    get_fel_numero_autorizacion() {
        return this.fel_numero_autorizacion;
    },
    set_plazo(plazo) {
        this.plazo = plazo;
    },
    get_plazo() {
        return this.plazo;
    },
    set_tipo_flujo(tipo_flujo) {
        this.tipo_flujo = tipo_flujo;
    },
    get_tipo_flujo() {
        return this.tipo_flujo;
    },
    set_cuota_autorizada(cuota_autorizada) {
        this.cuota_autorizada = cuota_autorizada;
    },
    get_cuota_autorizada() {
        return this.cuota_autorizada;
    },
    set_documento_personal_identificacion(documento_personal_identificacion) {
        this.documento_personal_identificacion = documento_personal_identificacion;
    },
    get_documento_personal_identificacion() {
        return this.documento_personal_identificacion;
    },
    set_cliente_vat(vat) {
        this.cliente_vat = vat;
    },
    get_cliente_vat() {
        return this.cliente_vat;
    },
    set_cliente_dpi(dpi) {
        this.cliente_dpi = dpi;
    },
    get_cliente_dpi() {
        return this.cliente_dpi;
    },
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.invoice_number = this.get_invoice_number() || false;
        json.fel_serie = this.get_fel_serie() || false;
        json.fel_numero = this.get_fel_numero() || false;
        json.fel_numero_autorizacion = this.get_fel_numero_autorizacion() || false;
        json.plazo = this.get_plazo() || false;
        json.tipo_flujo = this.get_tipo_flujo() || false;
        json.cuota_autorizada = this.get_cuota_autorizada() || false;
        json.documento_personal_identificacion = this.get_documento_personal_identificacion() || false;
        json.cliente_vat = this.get_cliente_vat() || false;
        json.cliente_dpi = this.get_cliente_dpi() || false;
        return json;
    },
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.invoice_number = json.invoice_number || false;
        this.fel_serie = json.fel_serie || false;
        this.fel_numero = json.fel_numero || false;
        this.fel_numero_autorizacion = json.fel_numero_autorizacion || false;
        this.plazo = json.plazo || false;
        this.tipo_flujo = json.tipo_flujo || false;
        this.cuota_autorizada = json.cuota_autorizada || false;
        this.documento_personal_identificacion = json.documento_personal_identificacion || false;
        this.cliente_vat = json.cliente_vat || false;
        this.cliente_dpi = json.cliente_dpi || false;
    },
    export_for_printing() {
        const json = super.export_for_printing(...arguments);
        json.invoice_number = this.get_invoice_number() || 0;
        json.fel_serie = this.get_fel_serie() || '';
        json.fel_numero = this.get_fel_numero() || '';
        json.fel_numero_autorizacion = this.get_fel_numero_autorizacion() || '';
        json.plazo = this.get_plazo() || '';
        json.tipo_flujo = this.get_tipo_flujo() || '';
        json.cuota_autorizada = this.get_cuota_autorizada() || '';
        json.documento_personal_identificacion = this.get_documento_personal_identificacion() || '';
        json.cliente_vat = this.get_cliente_vat() || '';
        json.cliente_dpi = this.get_cliente_dpi() || '';
        return json;
    },
});
