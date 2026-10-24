/** @odoo-module **/

import { Chatter } from "@mail/core/web/chatter";
import { patch } from "@web/core/utils/patch";

patch(Chatter.prototype, {
    async onUploaded(data) {
        await super.onUploaded(data);
        // Dar tiempo al servidor para que confirme el message_post del link de Backblaze,
        // luego refrescar la lista de mensajes del chatter para mostrar el enlace.
        setTimeout(() => {
            if (this.state.thread) {
                this.load(this.state.thread, ["messages"]);
            }
        }, 1000);
    },
});