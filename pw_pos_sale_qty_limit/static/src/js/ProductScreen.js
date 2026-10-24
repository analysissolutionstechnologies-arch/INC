/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { _t } from "@web/core/l10n/translation";
import { Order } from "@point_of_sale/app/store/models";


patch(Order.prototype, {
    async pay() {
        let product_list = [];
        this.get_orderlines().forEach(function(line) {
            let restrict_qty = line.product.pw_max_qty || line.product.categ.pw_max_qty;
            if ((line.product.pw_sale_limit && line.product.pw_max_qty < line.quantity) || line.product.categ.pw_sale_limit && line.product.categ.pw_max_qty < line.quantity) {
                product_list.push(line.product.display_name + ' sale limit '+ restrict_qty.toString() + ' Qty \n')
            }
        });
        if (this.pos.config.pw_restrict_sale_qty && product_list.length > 0){
            this.env.services.popup.add(ErrorPopup, {
                title: _t("Sale Qty Restriction"),
                body: _t(product_list),
            });
            return false;
        } else {
            return super.pay(...arguments);
        }
    },
});
