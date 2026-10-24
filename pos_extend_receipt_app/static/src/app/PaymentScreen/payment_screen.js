/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";

import { _t } from "@web/core/l10n/translation";
import { parseFloat } from "@web/views/fields/parsers";
import { useErrorHandlers, useAsyncLockedMethod } from "@point_of_sale/app/utils/hooks";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { DatePickerPopup } from "@point_of_sale/app/utils/date_picker_popup/date_picker_popup";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";
import { ConnectionLostError } from "@web/core/network/rpc_service";

import { PaymentScreenPaymentLines } from "@point_of_sale/app/screens/payment_screen/payment_lines/payment_lines";
import { PaymentScreenStatus } from "@point_of_sale/app/screens/payment_screen/payment_status/payment_status";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Component, useState, useRef } from "@odoo/owl";
import { renderToElement } from "@web/core/utils/render";
import { Numpad } from "@point_of_sale/app/generic_components/numpad/numpad";
import { floatIsZero } from "@web/core/utils/numbers";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
    },
    async _finalizeValidation() {
        debugger
        var self = this;
        if (this.currentOrder.is_paid_with_cash() || this.currentOrder.get_change()) {
            this.hardwareProxy.openCashbox();
        }
        var domain = [['pos_reference', '=', this.currentOrder['name']]]
        var fields = ['account_move', 'fel_serie', 'fel_numero', 'fel_numero_autorizacion'];
        this.currentOrder.date_order = luxon.DateTime.now();
        for (const line of this.paymentLines) {
            if (!line.amount === 0) {
                this.currentOrder.remove_paymentline(line);
            }
        }
        this.currentOrder.finalized = true;

        // 1. Save order to server.
        const syncOrderResult = await this.pos.push_single_order(this.currentOrder);

        if (syncOrderResult instanceof ConnectionLostError) {
            this.pos.showScreen(this.nextScreen);
            return;
        } else if (!syncOrderResult) {
            return;
        }

        try {
            // 2. Invoice.
            if (this.shouldDownloadInvoice() && this.currentOrder.is_to_invoice()) {
                if (syncOrderResult[0]?.account_move) {
                    await this.report.doAction("account.account_invoices", [
                        syncOrderResult[0].account_move,
                    ]);
                } else {
                    throw {
                        code: 401,
                        message: "Backend Invoice",
                        data: { order: this.currentOrder },
                    };
                }
            }
        } catch (error) {
            if (error instanceof ConnectionLostError) {
                Promise.reject(error);
                return error;
            } else {
                throw error;
            }
        }
        if(this.pos.config.invoice_number){
            if (this.currentOrder.is_to_invoice()) {
                await this.orm.call(
                    "pos.order",
                    "search_read",
                    [domain, ['account_move', 'partner_id']],
                ).then(async function (output) {
                    var inv_print = output[0]['account_move'][1].split(" ")[0];
                    self.currentOrder.set_invoice_number(inv_print);
                    
                    // Obtener los campos de account.move
                    if (output[0]['account_move']) {
                        const move_id = output[0]['account_move'][0];
                        const move_data = await self.orm.call(
                            "account.move",
                            "search_read",
                            [[['id', '=', move_id]], ['fel_serie', 'fel_numero', 'fel_numero_autorizacion', 'Plazo', 'TipoFlujo', 'cuota_autorizada']]
                        );
                        if (move_data && move_data[0]) {
                            self.currentOrder.set_fel_serie(move_data[0]['fel_serie'] || '');
                            self.currentOrder.set_fel_numero(move_data[0]['fel_numero'] || '');
                            self.currentOrder.set_fel_numero_autorizacion(move_data[0]['fel_numero_autorizacion'] || '');
                            self.currentOrder.set_plazo(move_data[0]['Plazo'] || '');
                            self.currentOrder.set_tipo_flujo(move_data[0]['TipoFlujo'] || '');
                            self.currentOrder.set_cuota_autorizada(move_data[0]['cuota_autorizada'] || '');
                        }
                    }

                    // Obtener los campos adicionales del cliente
                    if (output[0]['partner_id']) {
                        const partner_id = output[0]['partner_id'][0];
                        const partner_data = await self.orm.call(
                            "res.partner",
                            "search_read",
                            [[['id', '=', partner_id]], ['vat', 'documento_personal_identificacion']]
                        );
                        if (partner_data && partner_data[0]) {
                            self.currentOrder.set_cliente_vat(partner_data[0]['vat'] || '');
                            self.currentOrder.set_cliente_dpi(partner_data[0]['documento_personal_identificacion'] || '');
                        }
                    }
                })
            }
        }
        // 3. Post process.
        if (
            syncOrderResult &&
            syncOrderResult.length > 0 &&
            this.currentOrder.wait_for_push_order()
        ) {
            await this.postPushOrderResolve(syncOrderResult.map((res) => res.id));
        }

        await this.afterOrderValidation(!!syncOrderResult && syncOrderResult.length > 0);
    }
});
