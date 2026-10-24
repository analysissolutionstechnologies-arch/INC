/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { SaleOrderRow } from "@pos_sale/app/order_management_screen/sale_order_row/sale_order_row";

patch(SaleOrderRow.prototype, {
    get warehouse_names() {
        if (!this.order || !this.order.warehouse_names || !this.order.order_line) {
            return "";
        }
    
        const warehouseList = [];
    
        for (let lineId of this.order.order_line) {
            if (this.order.warehouse_names[lineId]) {
                warehouseList.push(this.order.warehouse_names[lineId]);
            }
        }
    
        return warehouseList.join(", ");
    }
})
