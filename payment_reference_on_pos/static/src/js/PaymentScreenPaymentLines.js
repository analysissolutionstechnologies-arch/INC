/** @odoo-module */

import { _t, _lt } from "@web/core/l10n/translation";
import { PaymentScreenPaymentLines } from "@point_of_sale/app/screens/payment_screen/payment_lines/payment_lines";
import { patch } from "@web/core/utils/patch";
import { PaymentReferencePopup } from "./PaymentReferencePopup";
import { useService } from "@web/core/utils/hooks";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";

patch(PaymentScreenPaymentLines.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
    },
    selectedLineClass(line) {
        if (line.name.startsWith('TC') || line.name.startsWith('TD')) {
            this.updatePaymentReference(line);
        }
        return Object.assign({}, super.selectedLineClass(line), {
            payment_reference: line.payment_reference,
            number_quote: line.number_quote,
            card_termination: line.card_termination,
            auth_number: line.auth_number,
            comment: line.comment,
            bank_id: line.bank_id,

        });
    },
    unselectedLineClass(line) {
        if (line.name.startsWith('TC') || line.name.startsWith('TD')) {
            this.updatePaymentReference(line);
        }
        return Object.assign({}, super.unselectedLineClass(line), {
            payment_reference: line.payment_reference,
            number_quote: line.number_quote,
            card_termination: line.card_termination,
            auth_number: line.auth_number,
            comment: line.comment,
            bank_id: line.bank_id,

        });
    },

    async updatePaymentReference(line) {        
        if (!line) {
            return;
        }
        debugger
        const bankIds = line.payment_method['bank_ids'];
        const bankRecords = await this.orm.call("res.bank", "get_bank_ids", [bankIds]);
        const startingBankId = bankRecords.length > 0 ? bankRecords[0].id : null;
        
        let isPopupComplete = false;
    
        while (!isPopupComplete) {
            debugger
            const { confirmed, payload: code } = await this.popup.add(PaymentReferencePopup, {
                startingValue: line.payment_reference,
                startingQuoteValue: line.number_quote,
                startingCardTerminationValue: line.card_termination,
                startingAuthNumberValue: line.auth_number,
                startingCommentValue: line.comment,
                bankIds: bankRecords,
                startingBankId: startingBankId,
                title: _t('Add / Update Payment Reference'),
            });
    
            if (!confirmed) {
                break;
            }
    
            if (!code.payment_reference || !code.number_quote || !code.auth_number || !code.bank_id) {
                await this.popup.add(ErrorPopup, {
                    title: _t('Error'),
                    body: _t("Todos los campos son obligatorios. Por favor, complete los campos faltantes."),
                });
                continue;
            }
    
            isPopupComplete = true;
            line.payment_reference = code.payment_reference;
            line.number_quote = code.number_quote;    
            line.card_termination = code.card_termination;    
            line.auth_number = code.auth_number;    
            line.comment = code.comment;    
            line.bank_id = code.bank_id;    
    
            console.log("=====line", line);
        }
    }
});
