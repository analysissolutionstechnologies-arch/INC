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
            query: "", busy: false,
        });
        this.incmdSearch = useRef("incmdSearch");
        this.incmdToggle = useRef("incmdToggle");
        useEffect(() => {
            if (this.incmdLauncher.open) {
                this.incmdSearch.el?.focus();
            } else {
                this.adapt();
            }
        }, () => [this.incmdLauncher.open]);
        useExternalListener(window, "keydown", (ev) => {
            if (ev.key === "Escape" && this.incmdLauncher.open) {
                ev.preventDefault();
                this.incmdCloseLauncher();
            }
        });
    },
    get incmdApps() {
        const normalize = (s) => (s || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase();
        const query = normalize(this.incmdLauncher.query.trim());
        return this.menuService.getApps().filter((app) => normalize(app.name).includes(query));
    },
    incmdToggleLauncher() {
        this.incmdLauncher.open = !this.incmdLauncher.open;
        this.incmdLauncher.query = "";
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
            this.incmdLauncher.query = "";
        } finally {
            this.incmdLauncher.busy = false;
        }
    },
});
