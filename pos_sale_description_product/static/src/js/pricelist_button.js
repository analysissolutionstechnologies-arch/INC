/** @odoo-module */
import { SetPricelistButton} from "@point_of_sale/app/screens/product_screen/control_buttons/pricelist_button/pricelist_button";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";

patch(SetPricelistButton.prototype, {
    async click() {
        const hasSaleOrderOrigin = this.currentOrder.orderlines.some(line => line.sale_order_origin_id);

        if (hasSaleOrderOrigin) {
            return;
        }
        
        const selectionList = this.pos.pricelists.map((pricelist) => ({
            id: pricelist.id,
            label: pricelist.name,
            isSelected:
                this.currentOrder.pricelist && pricelist.id === this.currentOrder.pricelist.id,
            item: pricelist,
        }));

        if (!this.pos.default_pricelist) {
            selectionList.push({
                id: null,
                label: _t("Default Price"),
                isSelected: !this.currentOrder.pricelist,
                item: null,
            });
        }

        const { confirmed, payload: selectedPricelist } = await this.popup.add(SelectionPopup, {
            title: _t("Select the pricelist"),
            list: selectionList,
        });

        if (confirmed) {
            this.currentOrder.set_pricelist(selectedPricelist);
        }
    }
});
