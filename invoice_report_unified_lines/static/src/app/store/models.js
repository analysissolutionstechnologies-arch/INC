/** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { omit } from "@web/core/utils/objects";

patch(Order.prototype, {
    export_for_printing() {
        const result = super.export_for_printing(...arguments);

        const hasMotoLine = this.orderlines.some((line) => line.product?.x_studio_es_moto_1);

        if (!hasMotoLine) {
            result.orderlines = this.orderlines.map((l) => omit(l.getDisplayData(), "internalNote"));
            return result;
        }

        const motoLine = this.orderlines.find((line) => line.product?.x_studio_es_moto_1);
        const totalPrice = this.orderlines.reduce((sum, line) => sum + line.get_display_price(), 0);
        const motoQty = motoLine ? motoLine.get_quantity() : 0;
        const motoUnitPrice = motoQty ? totalPrice / motoQty : totalPrice;

        const unifiedOrderlines = [];

        if (motoLine) {
            const motoDisplay = omit(motoLine.getDisplayData(), "internalNote");
            motoDisplay.price = this.env.utils.formatCurrency(totalPrice, this.currency);
            motoDisplay.unitPrice = this.env.utils.formatCurrency(motoUnitPrice, this.currency);
            unifiedOrderlines.push(motoDisplay);
        }

        for (const line of this.orderlines) {
            if (line === motoLine) {
                continue;
            }
            const lineDisplay = omit(line.getDisplayData(), "internalNote");
            lineDisplay.price = this.env.utils.formatCurrency(0, this.currency);
            lineDisplay.unitPrice = this.env.utils.formatCurrency(0, this.currency);
            unifiedOrderlines.push(lineDisplay);
        }

        result.orderlines = unifiedOrderlines;
        return result;
    },
});
