/** @odoo-module */

import { CashMovePopup } from "@point_of_sale/app/navbar/cash_move_popup/cash_move_popup";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { sprintf } from "@web/core/utils/strings";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { onWillStart, useState } from "@odoo/owl";

patch(CashMovePopup.prototype, {
    setup() {
        super.setup();
        this.info = useState({});
        onWillStart(async () => {
            this.info = await this.pos.getClosePosInfo();
        });
    },

    async confirm() {
        const output_amount = parseFloat(this.state.amount);
        const cash_in_box = this.info.default_cash_details.amount

        if (cash_in_box < output_amount && this.state.type == 'out') {
            this.popup.add(ErrorPopup, {
                title: _t("Validation Error"),
                body: sprintf(_t(
                    'You are trying to withdraw %s but only have %s in cash. '
                    + 'Please enter an amount less than or equal to the cash balance.',
                    this.env.utils.formatCurrency(output_amount),
                    this.env.utils.formatCurrency(cash_in_box),
                ))
            });
            return;
        }
        super.confirm();
    }

})
