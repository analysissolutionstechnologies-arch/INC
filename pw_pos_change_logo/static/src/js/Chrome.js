/** @odoo-module */

import { Navbar } from "@point_of_sale/app/navbar/navbar";
import { patch } from "@web/core/utils/patch";

patch(Navbar.prototype, {
    setup() {
        super.setup(...arguments);
    },
    get imageUrl() {
        return `/web/image?model=pos.config&field=pw_pos_logo&id=${this.pos.config.id}&unique=${this.pos.config.write_date}`;
    }
});
