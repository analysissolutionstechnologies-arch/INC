/** @odoo-module **/

import { SaleOrderManagementControlPanel } from "@pos_sale/app/order_management_screen/sale_order_management_control_panel/sale_order_management_control_panel";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";

// Guarda métodos originales ANTES del patch
const _originalSetup = SaleOrderManagementControlPanel.prototype.setup;
const _originalComputeDomain = SaleOrderManagementControlPanel.prototype._computeDomain;

patch(SaleOrderManagementControlPanel.prototype, {
    setup() {
        // Ejecuta SIEMPRE el setup original (crea pager, watchers, refs, etc.)
        if (typeof _originalSetup === "function") {
            _originalSetup.call(this, ...arguments);
        }

        // Servicios
        this.pos = this.pos || usePos();
        this.saleOrderFetcher = this.saleOrderFetcher || useService("sale_order_fetcher");

        // Servicio opcional (si no existe, no falla)
        try {
            this.customSaleOrderFetcher =
                this.customSaleOrderFetcher || useService("custom_sale_order_fetcher");
        } catch (_) {
            this.customSaleOrderFetcher = null;
        }

        // Precargar búsqueda por partner actual (si hay)
        const order = this.pos?.get_order?.();
        const partner = order?.get_partner?.();
        if (partner?.name && this.pos?.orderManagement) {
            this.pos.orderManagement.searchString = `"${partner.name}"`;
        }

        // Dominio inicial
        const domain = this._computeDomain();
        this.saleOrderFetcher?.setSearchDomain(domain);
        this.customSaleOrderFetcher?.setSearchDomain?.(domain);

        // Fallback: si algún otro patch impidió crear el pager, evita crash del template
        if (!this.pager) {
            this.pager = { paginationString: "" };
        }
    },

    _computeDomain() {
        const base =
            (typeof _originalComputeDomain === "function"
                ? _originalComputeDomain.call(this, ...arguments)
                : []) || [];
        // Solo ajusta el filtro de estado, respeta el resto del dominio
        return base.map((cond) =>
            Array.isArray(cond) && cond[0] === "state"
                ? ["state", "not in", ["cancel", "draft"]]
                : cond
        );
    },
});
