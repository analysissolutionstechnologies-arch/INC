/** @odoo-module */
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import {
    useState,
} from "@odoo/owl";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this.isProcessing = useState({ value: false });
        this.executionCount = useState({ value: 0 });
        this.buttonClickCount = useState({ value: 0 });
    },

    async validateOrder(isForceValidate) {
        debugger;
        this.buttonClickCount.value += 1;
        console.log(`🖱️ Botón presionado: ${this.buttonClickCount.value} veces`);
    
        if (this.isProcessing.value) {
            console.warn(`⚠️ La función ya está en ejecución. Intentos: ${this.executionCount.value}`);
            return;
        }
    
        this.isProcessing.value = true;
        this.executionCount.value += 1;
    
        console.log(`🔄 Ejecutando validateOrder - Intento número: ${this.executionCount.value}`);
    
        try {
            const currentOrder = this.pos.get_order();
            const originName = currentOrder.get_orderlines()?.[0]?.sale_order_origin_id?.name;
    
            if (originName) {
                try {
                    const pickings = await this.orm.call(
                        'stock.picking',
                        'search_read',
                        [[['origin', '=', originName]], ['id']]
                    );
                    if (pickings.length > 0) {
                        for (const picking of pickings) {
                            await this.orm.call('stock.picking', 'do_unreserve', [[picking.id]]);
                            console.log(`🧹 Se ejecutó do_unreserve para picking ID: ${picking.id}`);
                        }
                    } else {
                        console.warn(`📦 No se encontraron pickings con origin "${originName}".`);
                    }
                } catch (error) {
                    console.error("❌ Error al desreservar pickings:", error);
                }
            } else {
                console.warn("⚠️ No se encontró sale_order_origin_id.name en la orden. Continuando sin desreservar.");
            }
    
            const totalAmount = currentOrder.get_total_with_tax();
            console.log(`💵 Total de la orden actual: ${totalAmount}`);
    
            this.numberBuffer.capture();
    
            if (this.pos.config.cash_rounding) {
                if (!currentOrder.check_paymentlines_rounding()) {
                    this._display_popup_error_paymentlines_rounding();
                    return;
                }
            }
    
            if (await this._isOrderValid(isForceValidate)) {
                for (const line of this.paymentLines) {
                    if (!line.is_done()) {
                        currentOrder.remove_paymentline(line);
                    }
                }
                await this._finalizeValidation();
            }
    
        } finally {
            console.log("✅ Finalizando ejecución...");
            this.isProcessing.value = false;
        }
    }
    
});