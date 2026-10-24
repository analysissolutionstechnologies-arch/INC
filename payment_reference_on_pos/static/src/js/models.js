/** @odoo-module */

import { Payment } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Payment.prototype, {
    setup() {
        super.setup(...arguments);
        this.payment_reference = this.payment_reference || null;
        this.number_quote = this.number_quote || null;
        this.card_termination = this.card_termination || null;
        this.auth_number = this.auth_number || null;
        this.comment = this.comment || null;
        this.bank_id = this.bank_id || null;


    },
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.payment_reference = this.payment_reference;
        json.number_quote = this.number_quote;
        json.card_termination = this.card_termination;
        json.auth_number = this.auth_number;
        json.comment = this.comment;
        json.bank_id = this.bank_id;

        return json;
    },
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.payment_reference = json.payment_reference;
        this.number_quote = json.number_quote;
        this.card_termination = json.card_termination;
        this.auth_number = json.auth_number;
        this.comment = json.comment;
        this.bank_id = json.bank_id;

    },
});
  