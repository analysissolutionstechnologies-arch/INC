/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { SaleOrderRow } from "@pos_sale/app/order_management_screen/sale_order_row/sale_order_row";

patch(SaleOrderRow.prototype, {
    get line_names() {
        if (this.order && this.order.line_names && this.order.order_line) {
            for (let lineId of this.order.order_line) {

                if (this.order.line_names[lineId]) {
                    return this.order.line_names[lineId];
                }
            }
        }

    },
})
