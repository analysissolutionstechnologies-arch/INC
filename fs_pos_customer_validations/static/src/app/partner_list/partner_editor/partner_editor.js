/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { PartnerDetailsEdit } from "@point_of_sale/app/screens/partner_list/partner_editor/partner_editor";
import { patch } from "@web/core/utils/patch";

const REQUIRED_FIELDS = [
    { key: "name", message: _t("Se requiere un nombre de Cliente") },
    { key: "street", message: _t("Se requiere una direccion del Cliente") },
    { key: "city", message: _t("Se requiere la Ciudad del Cliente") },
    { key: "vat", message: _t("Se requiere el NIT del Cliente") },
];

function validateGuatemalanNIT(nit, ignoreCF = false) {
    nit = (nit || "CF").replace("-", "").toUpperCase();

    if (nit === "CF" && ignoreCF) return true;
    if (nit === "0" || nit === "" || nit.length > 11) return false;

    let sum = 0;
    let position = nit.length;
    const checkDigit = nit.slice(-1);
    const body = nit.slice(0, -1);

    for (const char of body) {
        const digit = parseInt(char, 10);
        if (isNaN(digit)) return false;
        sum += digit * position;
        position--;
    }

    const mod11 = Math.abs(11 - (sum % 11));
    const expectedCheckDigit = mod11 === 10 ? "K" : mod11 === 11 ? "0" : mod11.toString();

    return (body + expectedCheckDigit) === nit;
}

patch(PartnerDetailsEdit.prototype, {
    saveChanges() {
        const processedChanges = Object.fromEntries(
            Object.entries(this.changes).map(([key, value]) => [
                key,
                this.intFields.includes(key) ? parseInt(value) || false : value,
            ])
        );

        const invalidField = REQUIRED_FIELDS.find(
            field => (!this.props.partner[field.key] && !processedChanges[field.key]) || processedChanges[field.key] === ""
        );

        if (invalidField) {
            return this.popup.add(ErrorPopup, { title: invalidField.message });
        }

        if (processedChanges.state_id && 
            this.pos.states.find(state => state.id === processedChanges.state_id).country_id[0] !== processedChanges.country_id
        ) {
            processedChanges.state_id = false;
        }

        // Permitir el valor "CF" sin símbolos ni validación adicional
        if (!validateGuatemalanNIT(processedChanges.vat, true)) {
            return this.popup.add(ErrorPopup, { title: _t("El NIT ingresado no es válido, excepto 'CF'") });
        }

        processedChanges.id = this.props.partner.id || false;
        this.props.saveChanges(processedChanges);
    }
});
