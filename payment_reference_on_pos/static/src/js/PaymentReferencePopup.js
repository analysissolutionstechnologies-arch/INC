/** @odoo-module */

import { _t, _lt } from "@web/core/l10n/translation";
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { onMounted, useRef, useState } from "@odoo/owl";

export class PaymentReferencePopup extends AbstractAwaitablePopup {
    static template = "payment_reference_on_pos.PaymentReferencePopup";
    static defaultProps = {
        confirmText: _t("Ok"),
        cancelText: _t("Cancel"),
        title: '',
        body: '',
        startingValue: null,
        startingQuoteValue: null,
        startingCardTerminationValue: null,
        startingAuthNumberValue: null,
        startingCommentValue: null,
        bankIds: null,
        startingBankId: null,
        quoteOptions: [
            { value: 'corriente_1', label: 'Corriente' },
            { value: 'corriente_3', label: 'Plazo 3 Cuotas' },
            { value: 'corriente_6', label: 'Plazo 6 Cuotas' },
            { value: 'corriente_10', label: 'Plazo 10 Cuotas' },
            { value: 'corriente_12', label: 'Plazo 12 Cuotas' },
            { value: 'corriente_15', label: 'Plazo 15 Cuotas' },
            { value: 'corriente_18', label: 'Plazo 18 Cuotas' },
            { value: 'corriente_24', label: 'Plazo 24 Cuotas' },
            { value: 'corriente_36', label: 'Plazo 36 Cuotas' },
            { value: 'corriente_48', label: 'Plazo 48 Cuotas' },
        ],
    };

    setup() {
        super.setup();
        this.pos = usePos();
        this.inputRef = useRef('input');
        this.state = useState({ 
            inputValue: this.props.startingValue,
            quoteValue: this.props.startingQuoteValue,
            cardTerminationValue: this.props.startingCardTerminationValue, 
            authNumberValue: this.props.startingAuthNumberValue,
            commentValue: this.props.startingCommentValue,
            bankIdValue: this.props.startingBankId,
            selectedQuote: this.props.startingQuoteValue || 'corriente_3', // Asegurar el valor predeterminado
        });

        // Vinculamos el método de cambio del selector de cuotas
        this.onQuoteChange = this.onQuoteChange.bind(this);
    }

    mounted() {
        this.inputRef.el.focus();
    }

    // Método para manejar el cambio en el número de cuotas
    onQuoteChange(event) {
        this.state.selectedQuote = event.target.value; // Actualizar el valor de la cuota seleccionada
    }

    getPayload() {
        return {
            payment_reference: this.state.inputValue,
            number_quote: this.state.selectedQuote, // Cuota seleccionada
            card_termination: this.state.cardTerminationValue,
            auth_number: this.state.authNumberValue,
            comment: this.state.commentValue,
            bank_id: this.state.bankIdValue
        };
    }
}


