/** @odoo-module */

import { SaleOrderManagementControlPanel } from "@pos_sale/app/order_management_screen/sale_order_management_control_panel/sale_order_management_control_panel";
import { patch } from "@web/core/utils/patch";

patch(SaleOrderManagementControlPanel.prototype, {
    _computeDomain() {
        let domain = super._computeDomain(...arguments);
        console.log("domain", domain);

        // Modificar el dominio
        domain = domain.map(condition => {
            if (condition[0] === "state") {
                return ["state", "not in", ["cancel", "draft"]];
            }
            return condition;
        });
        console.log("domain edit", domain);
        return domain;
    }
});
