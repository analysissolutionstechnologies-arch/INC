/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

// Mapeo dinámico
let PRICE_LIST_PAYMENT_METHODS = {};

async function fetchPricelistPaymentMethods(self) {
    try {
        const rpc = self.env.services.rpc;
        const result = await rpc("/pos/pricelist_payment_methods", {});
        if (!result || !Array.isArray(result) || result.length === 0) {
            showPricelistWarning("No se pudo encontrar ningún método de pago para la lista de precios seleccionada.");
            PRICE_LIST_PAYMENT_METHODS = {};
            return false;
        }
        for (const row of result) {
            PRICE_LIST_PAYMENT_METHODS[row.pricelist_id] = row.payment_method_ids;
        }
        return true;
    } catch (error) {
        console.error("Error al obtener métodos de pago por lista de precios:", error);
        showPricelistWarning("Ocurrió un error al obtener los métodos de pago.");
        PRICE_LIST_PAYMENT_METHODS = {};
        return false;
    }
}

function showPricelistWarning(message) {
    let warningDiv = document.getElementById('pricelist-warning');
    if (!warningDiv) {
        warningDiv = document.createElement('div');
        warningDiv.id = 'pricelist-warning';
        warningDiv.style.position = 'fixed';
        warningDiv.style.top = '20px';
        warningDiv.style.left = '50%';
        warningDiv.style.transform = 'translateX(-50%)';
        warningDiv.style.background = '#dc3545'; // Rojo Bootstrap
        warningDiv.style.color = '#fff';
        warningDiv.style.padding = '12px 24px';
        warningDiv.style.borderRadius = '8px';
        warningDiv.style.zIndex = '9999';
        warningDiv.style.fontWeight = 'bold';
        document.body.appendChild(warningDiv);
    }
    warningDiv.textContent = message;
    // Quitar el mensaje después de 2 segundos
    setTimeout(() => {
        if (warningDiv && warningDiv.parentNode) {
            warningDiv.parentNode.removeChild(warningDiv);
        }
    }, 2000);
}

patch(PaymentScreen.prototype, {
    async setup() {
        await super.setup(...arguments);

        this.payment_methods_from_config = [];

        if (!this.pos) {
            return;
        }

        // Espera el fetch y luego filtra y renderiza
        const fetchOk = await fetchPricelistPaymentMethods(this);
        this.applyFilterAndInitializePaymentMethods(fetchOk);

        if (this.pos.config.is_auto_invoice) {
            this.currentOrder.set_to_invoice(true);
        }
    },

    get payment_methods() {
        return this.payment_methods_from_config;
    },

    applyFilterAndInitializePaymentMethods(fetchOk) {
        const currentOrder = this.pos.get_order();
        if (!currentOrder) {
            this.notification.add(_t("No se encontró una orden actual."));
            return;
        }

        if (fetchOk === false) {
            // No mostrar ningún método de pago si hubo error o está vacío
            this.payment_methods_from_config = [];
            this.render();
            return;
        }

        const selectedPricelist = currentOrder.pricelist;
        const pricelistId = selectedPricelist && (selectedPricelist.id || selectedPricelist['id']);

        const allPaymentMethods = this.pos.payment_methods?.filter(method =>
            this.pos.config.payment_method_ids.includes(method.id)
        );

        const allowedPaymentMethods = pricelistId && PRICE_LIST_PAYMENT_METHODS[pricelistId]
            ? allPaymentMethods.filter(method => PRICE_LIST_PAYMENT_METHODS[pricelistId].includes(method.id))
            : allPaymentMethods;

        // Si no hay métodos permitidos, mostrar advertencia y ocultar todos
        if (!allowedPaymentMethods || allowedPaymentMethods.length === 0) {
            showPricelistWarning("No se pudo encontrar ningún método de pago para la lista de precios seleccionada.");
            this.payment_methods_from_config = [];
        } else {
            // Oculta advertencia si todo está bien
            const warningDiv = document.getElementById('pricelist-warning');
            if (warningDiv) warningDiv.remove();
            this.payment_methods_from_config = allowedPaymentMethods;
        }
        this.render();
    },

    addNewPaymentLine(paymentMethod) {
        const currentOrder = this.pos.get_order();
        if (!currentOrder) {
            this.notification.add(_t("No se encontró una orden actual."));
            return;
        }
        const selectedPricelist = currentOrder.pricelist;
        const pricelistId = selectedPricelist && (selectedPricelist.id || selectedPricelist['id']);
        if (!PRICE_LIST_PAYMENT_METHODS || Object.keys(PRICE_LIST_PAYMENT_METHODS).length === 0) {
            this.notification.add(_t("No hay métodos de pago disponibles para la lista de precios seleccionada."));
            return;
        }
        if (pricelistId && PRICE_LIST_PAYMENT_METHODS[pricelistId]) {
            const allowedMethods = PRICE_LIST_PAYMENT_METHODS[pricelistId];
            if (!allowedMethods.includes(paymentMethod.id)) {
                this.notification.add(_t("Método de pago no permitido para la lista de precios seleccionada."));
                return;
            }
        }
        try {
            currentOrder.add_paymentline(paymentMethod);
            this.numberBuffer.reset();
        } catch (error) {
            this.notification.add(_t("Error al agregar una nueva línea de pago."));
        }
    },

});