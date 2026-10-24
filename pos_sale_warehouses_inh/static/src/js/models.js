/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { Orderline } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Orderline.prototype,{
    get_stock_location_name() {
        const superValue = super.get_stock_location_name();        
        if (superValue) {
            return superValue;
        }

        const lineId = this.sale_order_line_id?.id;
        if (!lineId) {
            return "";
        }

        if (
            this.sale_order_origin_id &&
            this.sale_order_origin_id.warehouse_names &&
            this.sale_order_origin_id.warehouse_names[lineId]
        ) {
            const warehouseData = this.sale_order_origin_id.warehouse_names[lineId];
            const warehouseName =
                typeof warehouseData === "object" ? warehouseData.name : warehouseData;
            this.stock_location_name = warehouseName || "";
        }

        return this.stock_location_name || "";
    },
});






