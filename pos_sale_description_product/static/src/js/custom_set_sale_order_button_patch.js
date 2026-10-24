/** @odoo-module */

import { SetSaleOrderButton } from "@pos_sale/app/set_sale_order_button/set_sale_order_button";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(SetSaleOrderButton.prototype, {
    async click() {
        // Obtén la orden actual
        const currentOrder = this.pos.get_order();

        // Verifica si la orden tiene líneas
        if (currentOrder && currentOrder.get_orderlines().length > 0) {
            // Muestra un mensaje en la pantalla
            this._showTemporaryMessage(
                _t("La orden actual tiene líneas. Por favor, elimínalas antes de continuar.")
            );
            return; // Detiene la ejecución posterior
        }

        // Si no hay líneas, ejecuta la lógica original
        this.pos.showScreen("SaleOrderManagementScreen");
    },

    // Función para mostrar un mensaje temporal
    _showTemporaryMessage(message) {
        const messageContainer = document.createElement("div");
        messageContainer.className = "pos-temporary-message";
        messageContainer.textContent = message;

        // Agrega el mensaje al DOM
        const posContainer = document.querySelector(".pos");
        if (posContainer) {
            posContainer.appendChild(messageContainer);

            // Elimina el mensaje después de 3 segundos
            setTimeout(() => {
                messageContainer.remove();
            }, 3000);
        }
    },
});






