/** @odoo-module */

import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";
export class CustomOrderTypeButtons extends Component {
    static template = "bi_pos_order_types.CustomOrderTypeButtons";

    setup() {
        this.pos = usePos();
    }
    is_available() {
	   const order = this.env.pos.get_order();
	   return order;
   	}

   	async onClick() {
		var order = this.pos.get_order();
		var orderlines = order.orderlines;
		if (orderlines.length === 0) {
			this.pos.popup.add(ErrorPopup,{
				title: _t('Orden vacía'),
				body: _t('Debe haber al menos un producto en su pedido antes de aplicar el tipo de pedido.'),
			});
			return;
		}
		else{
			let self = this;
			let lst = self.pos.pos_custom_order_type;
			let order = this.pos.get_order();

			const selectionList = this.pos.pos_custom_order_type.map(otype => ({
				id: otype.id,
				label: otype.name,
				isSelected:false,
				item: otype,
			}));

			const { confirmed, payload: selectedtype } = await this.pos.popup.add(
				SelectionPopup,
				{
					title: _t('Seleccione Tipos de pedido POS'),
					list: selectionList,
				}
			);

			if (confirmed) {
				order.set_order_type(selectedtype.name);
				order.set_order_type_id(selectedtype.id)
			}
		}
	}

    
}

ProductScreen.addControlButton({
    component: CustomOrderTypeButtons,
    position: ["before", "SetFiscalPositionButton"],
    condition: function () {
        return this.pos.config.enable_order_type;;
    },
});

