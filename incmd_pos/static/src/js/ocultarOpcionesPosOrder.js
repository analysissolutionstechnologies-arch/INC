/** @odoo-module */

import {TicketScreen} from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import {patch} from "@web/core/utils/patch";
import {_t} from "@web/core/l10n/translation";

patch(TicketScreen.prototype, {
    _getOrderStates() {
        const states = new Map();
        states.set("ONGOING", { text: _t("Ongoing") });
        return states;
    },
    _getFilterOptions() {
        return this._getOrderStates();
    }
});