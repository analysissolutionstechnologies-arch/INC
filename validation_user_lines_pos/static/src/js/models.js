/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";


patch(Order.prototype, {
    async pay() {
        const missingSeller = this.orderlines.some((line) => !line.user_id);

        if (missingSeller) {
            const { confirmed } = await this.env.services.popup.add(ConfirmPopup, {
                title: _t("Falta de empleado"),
                body: _t("Todas las lineas deben tener un empleado asociado para poder continuar."),
                confirmText: _t("OK"),
            });
            if (!confirmed || confirmed) {
                return;
            }
        }

        const sellers = this.orderlines.map((line) => line.user_id);
        const uniqueSellers = new Set(sellers);

        if (uniqueSellers.size > 1) {
            const { confirmed } = await this.env.services.popup.add(ConfirmPopup, {
                title: _t("Empleados Diferentes"),
                body: _t("Las líneas tienen empleados diferentes. Por favor, asegúrese de que todos los productos tengan el mismo empleado antes de continuar."),
                confirmText: _t("OK"),
            });
            if (!confirmed || confirmed) {
                return;
            }
        }

        await super.pay();
    }
})