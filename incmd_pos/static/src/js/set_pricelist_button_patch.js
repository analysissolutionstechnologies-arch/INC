/** @odoo-module */

import { SetPricelistButton } from "@point_of_sale/app/screens/product_screen/control_buttons/pricelist_button/pricelist_button";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";

// Parche para el botón de la lista de precios
patch(SetPricelistButton.prototype, {
    async click() {
        const hasSaleOrderOrigin = this.currentOrder.orderlines.some(line => line.sale_order_origin_id);

        if (hasSaleOrderOrigin) {
            return;
        }

        const selectionList = this.pos.pricelists.map((pricelist) => ({
            id: pricelist.id,
            label: pricelist.name,
            isSelected:
                this.currentOrder.pricelist && pricelist.id === this.currentOrder.pricelist.id,
            item: pricelist,
        }));

        if (!this.pos.default_pricelist) {
            selectionList.push({
                id: null,
                label: _t("Default Price"),
                isSelected: !this.currentOrder.pricelist,
                item: null,
            });
        }

        const { confirmed, payload: selectedPricelist } = await this.popup.add(SelectionPopup, {
            title: _t("Select the pricelist"),
            list: selectionList,
        });

        if (confirmed) {
            if (selectedPricelist && selectedPricelist.x_studio_reestriccion_pos) {
                // Mostrar mensaje en pantalla
                const warningDiv = document.createElement('div');
                warningDiv.id = 'pricelist-warning';
                warningDiv.textContent = "La lista de precios seleccionada no se puede usar.";
                warningDiv.style.position = 'fixed';
                warningDiv.style.top = '50%';
                warningDiv.style.left = '50%';
                warningDiv.style.transform = 'translate(-50%, -50%)';
                warningDiv.style.backgroundColor = 'rgba(255, 0, 0, 0.8)';
                warningDiv.style.color = 'white';
                warningDiv.style.padding = '20px';
                warningDiv.style.borderRadius = '5px';
                warningDiv.style.zIndex = '9999';

                document.body.appendChild(warningDiv);

                // Eliminar el mensaje después de 3 segundos
                setTimeout(() => {
                    document.body.removeChild(warningDiv);
                }, 1500);

                return; // Evitar que se asigne la lista
            }
            this.currentOrder.set_pricelist(selectedPricelist);
        }
    },
});