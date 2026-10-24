/** @odoo-module */

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
    },
    export_for_printing() {
        const result = super.export_for_printing(...arguments);
        result['headerData']['pw_change_logo'] = this.pos.config.pw_change_logo;
        result['headerData']['config_id'] = this.pos.config.id;
        return result;
    },
});
