/** @odoo-module */
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";


patch(PaymentScreen.prototype, {
    async selectPartner(isEditMode = false, missingFields = []) {
        debugger
        // IMPROVEMENT: This code snippet is repeated multiple times.
        // Maybe it's better to create a function for it.
        const hasSaleOrderOrigin = this.currentOrder.orderlines.some(
            (line) => line.sale_order_origin_id
        );
        if (hasSaleOrderOrigin) {
            return;
        }
        const currentPartner = this.currentOrder.get_partner();
        const partnerScreenProps = { partner: currentPartner };
        if (isEditMode && currentPartner) {
            partnerScreenProps.editModeProps = true;
            partnerScreenProps.missingFields = missingFields;
        }
        const { confirmed, payload: newPartner } = await this.pos.showTempScreen(
            "PartnerListScreen",
            partnerScreenProps
        );
        if (confirmed) {
            this.currentOrder.set_partner(newPartner);
        }
    }
});
