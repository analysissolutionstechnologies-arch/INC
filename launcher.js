/** @odoo-module **/
import { NavBar } from "@web/webclient/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { useState, useExternalListener, useRef, useEffect } from "@odoo/owl";

patch(NavBar.prototype, {
    setup() {
        super.setup(...arguments);
        const path = window.location.pathname.replace(/\/$/, "");
        const directAction = /(?:action|model|id)=/.test(window.location.hash + window.location.search);
        this.incmdLauncher = useState({
            open: ["/odoo", "/web"].includes(path) && !directAction,
            busy: false,
        });
        this.incmdToggle = useRef("incmdToggle");
        useEffect(() => {
            if (!this.incmdLauncher.open) this.adapt();
        }, () => [this.incmdLauncher.open]);
        useExternalListener(window, "keydown", (ev) => {
            if (ev.key === "Escape" && this.incmdLauncher.open) {
                ev.preventDefault();
                this.incmdCloseLauncher();
            }
        });
    },
    get incmdApps() {
        return this.menuService.getApps();
    },
    incmdToggleLauncher() {
        this.incmdLauncher.open = !this.incmdLauncher.open;

    },
    incmdCloseLauncher() {
        this.incmdLauncher.open = false;
        this.incmdToggle.el?.focus();
    },
    async incmdOpenApp(app) {
        if (this.incmdLauncher.busy) return;
        this.incmdLauncher.busy = true;
        try {
            await this.menuService.selectMenu(app);
            this.incmdLauncher.open = false;

        } finally {
            this.incmdLauncher.busy = false;
        }
    },
});
