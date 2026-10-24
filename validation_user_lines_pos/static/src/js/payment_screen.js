/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";

patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate) {
        const order = this.pos.get_order();
        const orderlines = order.get_orderlines();

        const missingSeller = orderlines.some((line) => !line.user_id);
        if (missingSeller) {
            const { confirmed } = await this.env.services.popup.add(ConfirmPopup, {
                title: _t("Falta de empleado"),
                body: _t("Todas las líneas deben tener un empleado asociado para poder continuar."),
                confirmText: _t("OK"),
            });
            return;
        }

        const sellers = orderlines.map((line) => line.user_id);
        const uniqueSellers = new Set(sellers.filter(Boolean));
        if (uniqueSellers.size > 1) {
            const { confirmed } = await this.env.services.popup.add(ConfirmPopup, {
                title: _t("Empleados Diferentes"),
                body: _t("Las líneas tienen empleados diferentes. Por favor, asegúrese de que todos los productos tengan el mismo empleado antes de continuar."),
                confirmText: _t("OK"),
            });
            return;
        }

        return await super.validateOrder(isForceValidate);
    },
});
