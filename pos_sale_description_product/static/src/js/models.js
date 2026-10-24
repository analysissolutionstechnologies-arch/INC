/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { Orderline } from "@point_of_sale/app/store/models";
patch(Orderline.prototype, {
    get_full_product_name() {
        if (this.sale_order_origin_id && this.sale_order_origin_id.line_names) {
            if (this.sale_order_origin_id.line_names[this.sale_order_line_id.id]) {
                let product = this.sale_order_origin_id.line_names[this.sale_order_line_id.id];
                return product
            }
        }
        return this.full_product_name || this.product.display_name;
    }
    
})
