/** @odoo-module */

import {PaymentScreen} from "@point_of_sale/app/screens/payment_screen/payment_screen";
import {patch} from "@web/core/utils/patch";
import {onMounted} from "@odoo/owl";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        onMounted(() => {
            if (this.pos.config.hide_invoice_button) {
                let js_invoice = document.getElementsByClassName('js_invoice');
                (js_invoice.length > 0) && (js_invoice[0].style.visibility = 'hidden');
            }
        });
    }
});
