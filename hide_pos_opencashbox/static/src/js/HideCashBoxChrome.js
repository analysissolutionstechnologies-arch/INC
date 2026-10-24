/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
    /**
     * @override
     */
    shouldShowCashControl() {
        // Hide Open Cash Control based on hide_pos_opencashbox configuration
        if (this.config.hide_pos_opencashbox) {
            return false;
        }
        return super.shouldShowCashControl(...arguments);
    },
});
