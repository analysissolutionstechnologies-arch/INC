/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { Order } from "@point_of_sale/app/store/models";

// Sobrescribe la función y omite el set_pricelist
patch(Order.prototype, {
    updatePricelistAndFiscalPosition(newPartner) {
        let newPartnerPricelist, newPartnerFiscalPosition;
        const defaultFiscalPosition = this.pos.fiscal_positions.find(
            (position) => position.id === this.pos.config.default_fiscal_position_id[0]
        );
        if (newPartner) {
            newPartnerFiscalPosition = newPartner.property_account_position_id
                ? this.pos.fiscal_positions.find(
                    (position) => position.id === newPartner.property_account_position_id[0]
                )
                : defaultFiscalPosition;
            newPartnerPricelist = this.pos.pricelists.find(
                (pricelist) => pricelist.id === newPartner.property_product_pricelist[0]
            ) || this.pos.default_pricelist;
        } else {
            newPartnerFiscalPosition = defaultFiscalPosition;
            newPartnerPricelist = this.pos.default_pricelist;
        }
        this.set_fiscal_position(newPartnerFiscalPosition);
        // this.set_pricelist(newPartnerPricelist); // <--- OMITIDO
    }
});