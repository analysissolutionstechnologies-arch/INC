/** @odoo-module **/
import { Chatter } from "@mail/chatter/web_portal/chatter";
import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class RequestsWorkspace extends Component {
    static components = { Chatter };
    static template = "incmd_requests.Workspace";
    static props = ["*"];
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.actionService = useService("action");
        const params = this.props.action?.params || {};
        this.state = useState({
            boot: null, busy: false, error: "", page: params.page || "list", mode: params.mode || "mine",
            records: [], total: 0, offset: 0, query: "", status: "", unit: "", origin: "", process: "",
            columns: [], detail: null, timelineTab: "messages", comment: "", responsible: "", files: [],
            form: { id: false, unit_id: "", reason_id: "", name: "", description: "", original_attachment_ids: [] },
            config: null, section: params.section || "units", editor: null, stageEditor: null,
            flowTab: "stages", confirmTransition: null, viewBack: "list", sortNewest: true,
        });
        this.listGeneration = 0;
        onWillStart(() => this.run(async () => {
            await this.refreshBootstrap();
            if (this.state.page === "config") await this.loadConfiguration();
            else await this.loadList();
        }));
    }
    async run(callback) {
        if (this.state.busy) return;
        this.state.busy = true; this.state.error = "";
        try { return await callback(); }
        catch (error) {
            const message = error.data?.message || error.message || "No fue posible completar la operación.";
            this.state.error = message;
            this.notification.add(message, { type: "danger" });
        } finally { this.state.busy = false; }
    }
    async refreshBootstrap() { this.state.boot = await this.orm.call("incmd.request", "ui_bootstrap", []); }
    options() {
        return { mode: this.state.mode, query: this.state.query, status: this.state.status,
            unit_id: Number(this.state.unit) || false, origin_id: Number(this.state.origin) || false,
            process_id: Number(this.state.process) || false, offset: this.state.offset };
    }
    async loadList() {
        const generation = ++this.listGeneration;
        const result = await this.orm.call("incmd.request", "ui_list", [this.options()]);
        if (generation === this.listGeneration) Object.assign(this.state, result);
    }
    searchKey(ev) { if (ev.key === "Enter") this.filter(); }
    rowKey(ev,id) { if (ev.key === "Enter") this.openRecord(id); }
    async filter() { this.state.offset = 0; await this.run(() => this.state.page === "board" ? this.loadBoard() : this.loadList()); }
    async pageBy(delta) { this.state.offset = Math.max(0, this.state.offset + delta * 40); await this.run(() => this.loadList()); }
    async changeMode(mode) { this.state.mode = mode; this.state.offset = 0; await this.filter(); }
    get title() {
        if (this.state.page === "config") return this.sectionTitle;
        if (this.state.page === "new") return this.state.form.id ? "Editar borrador" : "Nueva solicitud";
        if (this.state.page === "detail") return this.state.detail?.number || "Seguimiento";
        if (this.state.page === "board") return "Bandeja del área";
        return { mine: "Mis solicitudes", inbox: "Bandeja de atención", supervision: "Solicitudes de mis áreas y tiendas" }[this.state.mode];
    }
    get receivingUnits() { return (this.state.boot?.units || []).filter(u => u.receives); }
    get formReasons() { return (this.state.boot?.reasons || []).filter(r => r.unit_id[0] === Number(this.state.form.unit_id)); }
    get boardProcesses() { return (this.state.boot?.processes || []).filter(p => p.state === "published" && (!this.state.unit || p.unit_id[0] === Number(this.state.unit))); }
    get currentProcess() { return (this.state.boot?.processes || []).find(p => p.id === Number(this.state.process)); }
    get formReason() { return this.formReasons.find(r => r.id === Number(this.state.form.reason_id)); }
    get stages() { return this.state.detail?.stages || []; }
    label(value) { return value ? value[1] : "—"; }
    initials(name) { return String(name || "").split(" ").filter(Boolean).slice(0, 2).map(s => s[0]).join("").toUpperCase(); }
    date(value, time = false) {
        if (!value) return "—";
        const d = new Date(String(value).replace(" ", "T") + (String(value).endsWith("Z") ? "" : "Z"));
        if (Number.isNaN(d.getTime())) return String(value);
        return new Intl.DateTimeFormat("es-GT", { dateStyle: "short", ...(time ? { timeStyle: "short" } : {}) }).format(d);
    }
    age(value) {
        if (!value) return "";
        const hours = Math.max(0, Math.floor((Date.now() - new Date(String(value).replace(" ", "T") + "Z").getTime()) / 3600000));
        return hours < 24 ? `Hace ${hours || 1} ${hours === 1 || !hours ? "hora" : "horas"}` : `Hace ${Math.floor(hours / 24)} días`;
    }
    statusName(value) { return { draft: "Borrador", open: "En atención", done: "Finalizada", rejected: "Rechazada" }[value] || value; }
    download(id) { return `/web/content/${Number(id)}?download=true`; }
    bytes(size) { return size >= 1048576 ? `${(size / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round((size || 0) / 1024))} KB`; }
    attachment(id) { return this.state.detail?.attachments.find(a => a.id === id) || { id, name: "Documento", file_size: 0 }; }
    text(html) { const doc = new DOMParser().parseFromString(html || "", "text/html"); return doc.body.textContent || ""; }
    get timeline() {
        const d = this.state.detail; if (!d) return [];
        const entries = [
            ...d.history.map(h => ({ key: `h${h.id}`, name: this.label(h.user_id), date: h.create_date, title: h.action, text: h.comment, attachments: h.attachment_ids })),
            ...d.messages.map(m => ({ key: `m${m.id}`, name: this.label(m.author_id), date: m.date, title: "Comentario", text: this.text(m.body), attachments: m.attachment_ids })),
        ];
        return entries.sort((a, b) => this.state.sortNewest ? b.date.localeCompare(a.date) : a.date.localeCompare(b.date));
    }
    async showList() { await this.run(async () => { this.state.page = "list"; await this.loadList(); }); }
    async newRequest() {
        await this.run(async () => {
            await this.refreshBootstrap();
            this.state.form = { id: false, unit_id: "", reason_id: "", name: "", description: "", original_attachment_ids: [] };
            this.state.files = []; this.pendingAttachments = []; this.state.detail = null; this.state.page = "new";
        });
    }
    changeFormUnit(ev) { this.state.form.unit_id = ev.target.value; this.state.form.reason_id = ""; }
    async openRecord(id) {
        await this.run(async () => {
            const d = await this.orm.call("incmd.request", "ui_detail", [[id]]);
            this.state.viewBack = this.state.page === "board" ? "board" : "list";
            this.state.detail = d; this.pendingAttachments = []; this.state.files = []; this.state.comment = ""; this.state.responsible = "";
            if (d.state === "draft" && d.is_owner) {
                this.state.form = { id: d.id, unit_id: String(d.unit_id[0]), reason_id: String(d.reason_id[0]), name: d.name,
                    description: d.description, original_attachment_ids: [...d.original_attachment_ids] };
                this.state.page = "new";
            } else this.state.page = "detail";
        });
    }
    async redirectRequest() {
        const id = this.state.detail.id;
        const action = await this.orm.call("incmd.request", "action_redirect", [[id]]);
        await this.actionService.doAction(action, { onClose: async () => {
            this.state.detail = null; this.state.page = "list";
            await this.run(async () => { await this.refreshBootstrap(); await this.loadList(); });
        }});
    }
    async readFiles(ev) {
        const input = ev.target;
        await this.run(async () => {
            const files = Array.from(input.files || []);
            const result = [];
            for (const file of files) {
                if (file.size > 25 * 1048576) throw new Error(`El archivo ${file.name} supera 25 MB. Divídalo antes de adjuntarlo.`);
                const data = await new Promise((resolve, reject) => {
                    const reader = new FileReader(); reader.onload = () => resolve(String(reader.result).split(",")[1]);
                    reader.onerror = () => reject(new Error("No se pudo leer el archivo.")); reader.readAsDataURL(file);
                });
                result.push({ key: `${Date.now()}-${Math.random()}`, name: file.name, size: file.size, mimetype: file.type || "application/octet-stream", data });
            }
            this.state.files.push(...result);
        });
        input.value = "";
    }
    removeFile(key) { this.state.files = this.state.files.filter(f => f.key !== key); }
    async uploadFiles(requestId) {
        const ids = [];
        // Cada carga exitosa se retira de la cola: un reintento no la duplica.
        for (const file of [...this.state.files]) {
            const created = await this.orm.create("ir.attachment", [{ name: file.name, datas: file.data,
                mimetype: file.mimetype, res_model: "incmd.request", res_id: requestId }]);
            ids.push(created[0]); this.state.files = this.state.files.filter(f => f.key !== file.key);
            this.pendingAttachments = [...(this.pendingAttachments || []), created[0]];
        }
        return ids;
    }
    async saveDraft(submit = false) {
        await this.run(async () => {
            const form = this.state.form;
            if (!form.name.trim() || !form.description.trim() || !form.unit_id || !form.reason_id) throw new Error("Complete área, motivo, asunto y descripción.");
            if (!this.state.boot.origin) throw new Error("El administrador debe asignarle un área o tienda desde Empleados o Usuarios y perfiles.");
            const values = { name: form.name.trim(), description: form.description.trim(), unit_id: Number(form.unit_id), reason_id: Number(form.reason_id) };
            if (form.id) await this.orm.write("incmd.request", [form.id], values);
            else form.id = (await this.orm.create("incmd.request", [values]))[0];
            await this.uploadFiles(form.id);
            if (this.pendingAttachments?.length) {
                const ids = [...new Set([...form.original_attachment_ids, ...this.pendingAttachments])];
                await this.orm.write("incmd.request", [form.id], { original_attachment_ids: [[6, 0, ids]] });
                form.original_attachment_ids = ids; this.pendingAttachments = [];
            }
            if (submit) {
                if (!window.confirm("Al enviar se bloquearán los datos y adjuntos originales. ¿Enviar solicitud?")) return;
                await this.orm.call("incmd.request", "action_submit", [[form.id]]);
                this.state.detail = await this.orm.call("incmd.request", "ui_detail", [[form.id]]);
                this.state.page = "detail";
            }
            this.notification.add(submit ? "Solicitud enviada." : "Borrador guardado.", { type: "success" });
        });
    }
    async back() {
        if (this.state.page === "new" && (this.state.form.name || this.state.files.length) && !window.confirm("¿Volver a la bandeja? Los cambios sin guardar se perderán.")) return;
        await this.run(async () => {
            this.state.page = this.state.viewBack;
            this.state.files = []; this.pendingAttachments = [];
            if (this.state.page === "board") await this.loadBoard(); else await this.loadList();
        });
    }
    async followup(transition = false) {
        await this.run(async () => {
            const d = this.state.detail;
            if (!this.state.comment.trim()) throw new Error("Escriba el comentario de avance o aclaración.");
            if (transition && d.attachment_required && !this.state.files.length && !this.pendingAttachments?.length) throw new Error("Esta etapa requiere adjuntar una evidencia nueva.");
            if (transition && !window.confirm(`¿${transition.name}? El cambio quedará registrado en el historial.`)) return;
            await this.uploadFiles(d.id);
            const wizard = (await this.orm.create("incmd.request.action", [{ request_id: d.id,
                comment: this.state.comment.trim(), transition_id: transition ? transition.id : false,
                responsible_id: d.can_handle ? Number(this.state.responsible) || false : false,
                attachment_ids: [[6, 0, this.pendingAttachments || []]] }]))[0];
            await this.orm.call("incmd.request.action", "action_apply", [[wizard]]);
            this.pendingAttachments = []; this.state.comment = ""; this.state.responsible = "";
            this.state.detail = await this.orm.call("incmd.request", "ui_detail", [[d.id]]);
            this.notification.add("Seguimiento registrado.", { type: "success" });
        });
    }
    requestClarification() { this.state.comment = "Se solicita aclaración: "; document.querySelector(".ir_followup_text")?.focus(); }
    async showBoard() {
        await this.run(async () => {
            this.state.status = "";
            if (this.state.detail?.process_id && this.state.page === "detail") {
                this.state.process = String(this.state.detail.process_id[0]); this.state.unit = "";
            }
            if (!this.state.process && this.boardProcesses.length) this.state.process = String(this.boardProcesses[0].id);
            this.state.page = "board"; await this.loadBoard();
        });
    }
    async loadBoard() {
        if (!this.state.process) { this.state.columns = []; return; }
        const result = await this.orm.call("incmd.request", "ui_board", [Number(this.state.process), this.options()]);
        this.state.columns = result.columns;
    }
    async changeBoardUnit() { this.state.process = ""; if (this.boardProcesses.length) this.state.process = String(this.boardProcesses[0].id); await this.filter(); }
    get configSections() {
        return [{ key: "units", name: "Áreas y tiendas", icon: "building" }, { key: "assignments", name: "Usuarios y perfiles", icon: "users" },
            { key: "reasons", name: "Motivos", icon: "tags" }, { key: "processes", name: "Procesos y versiones", icon: "sitemap" }];
    }
    get sectionTitle() { return this.configSections.find(s => s.key === this.state.section)?.name || "Configuración"; }
    async loadConfiguration() {
        if (!this.state.boot.admin) throw new Error("Solo el administrador puede acceder a Configuración.");
        this.state.config = await this.orm.call("incmd.request", "ui_configuration", []);
    }
    async switchSection(key) { await this.run(async () => { this.state.section = key; this.state.editor = null; this.state.stageEditor = null; await this.loadConfiguration(); }); }
    get configRows() { return this.state.config?.[this.state.section] || []; }
    defaults(kind) {
        return {
            units: { name: "", kind: "area", receives: true, active: true, department_id: "", member_ids: [], supervisor_ids: [] },
            assignments: { user_id: "", unit_id: "", role: "user" },
            reasons: { name: "", unit_id: "", process_id: "", description: "", active: true },
            processes: { name: "", unit_id: "", version: 1 },
            stages: { name: "", sequence: (this.processStages.length + 1) * 10, process_id: this.state.editor?.id,
                is_initial: false, is_closed: false, requires_approval: false, attachment_required: false, actor_type: "team", actor_ids: [] },
            transitions: { name: "", sequence: 10, process_id: this.state.editor?.id, from_stage_id: "", to_stage_id: "", kind: "advance" },
        }[kind];
    }
    editConfig(row = null) {
        const values = row ? structuredClone(JSON.parse(JSON.stringify(row))) : this.defaults(this.state.section);
        for (const key of ["unit_id", "user_id", "process_id", "department_id"]) if (Array.isArray(values[key])) values[key] = values[key][0];
        this.state.editor = { id: row?.id || false, kind: this.state.section, values, published: row?.state === "published" };
        this.state.stageEditor = null;
    }
    get configFields() { return this.fieldsFor(this.state.editor?.kind); }
    fieldsFor(kind) {
        const f = (key, label, type = "text", options = []) => ({ key, label, type, options });
        const cfg = this.state.config || {};
        const pairs = (items) => (items || []).map(x => ({ id: x.id, name: x.display_title || x.name }));
        const activeUnits = (cfg.units || []).filter(u => u.active);
        const unitOptions = pairs(activeUnits); const areas = pairs(activeUnits.filter(u => u.receives));
        const activeEditor = ["stages","transitions"].includes(kind) ? this.state.stageEditor : this.state.editor;
        const areaId = Number(activeEditor?.values.unit_id);
        if (kind === "units") return [f("name", "Nombre *"), f("kind", "Tipo", "select", [{ id: "area", name: "Área" }, { id: "store", name: "Tienda" }]),
            f("department_id", "Departamento de Empleados", "select", pairs(cfg.departments)), f("receives", "Recibe solicitudes", "toggle"),
            f("active", "Activo", "toggle"), f("member_ids", "Equipo de atención", "multi", pairs(cfg.users)), f("supervisor_ids", "Supervisores a cargo", "multi", pairs(cfg.users))];
        if (kind === "assignments") return [f("user_id", "Usuario *", "select", pairs(cfg.users)), f("unit_id", "Área o tienda *", "select", unitOptions),
            f("role", "Perfil del módulo", "select", [{ id: "user", name: "Usuario" }, { id: "supervisor", name: "Supervisor" }, { id: "admin", name: "Administrador" }])];
        if (kind === "reasons") return [f("name", "Nombre *"), f("unit_id", "Área destinataria *", "select", areas), f("process_id", "Proceso publicado *", "select",
            pairs((cfg.processes || []).filter(p => p.state === "published" && p.unit_id[0] === areaId))), f("description", "Descripción e instrucciones", "textarea"), f("active", "Activo", "toggle")];
        if (kind === "processes") return [f("name", "Nombre *"), f("unit_id", "Área *", "select", areas), f("version", "Versión", "number")];
        if (kind === "stages") return [f("name", "Etapa *"), f("sequence", "Orden", "number"),
            f("actor_type", "Responsable de la etapa", "select", [{ id: "team", name: "Equipo destinatario" }, { id: "origin_supervisor", name: "Supervisor de origen" }, { id: "users", name: "Usuarios específicos" }]),
            ...(activeEditor?.values.actor_type === "users" ? [f("actor_ids", "Usuarios autorizados *", "multi", pairs(cfg.users))] : []),
            f("is_initial", "Etapa inicial", "toggle"), f("requires_approval", "Requiere aprobación", "toggle"),
            f("attachment_required", "Adjunto obligatorio", "toggle"), f("is_closed", "Etapa de cierre", "toggle")];
        if (kind === "transitions") return [f("name", "Acción *"), f("sequence", "Orden", "number"), f("from_stage_id", "Desde *", "select", pairs(this.processStages.filter(s => !s.is_closed))),
            f("to_stage_id", "Destino *", "select", pairs(this.processStages)), f("kind", "Tipo de acción", "select", [{ id: "advance", name: "Avanzar" }, { id: "approve", name: "Aprobar" }, { id: "return", name: "Devolver" }, { id: "reject", name: "Rechazar" }])];
        return [];
    }
    setConfigValue(ev, field, nested = false) {
        const values = (nested ? this.state.stageEditor : this.state.editor).values;
        let value = ev.target.value;
        if (field.type === "toggle") value = ev.target.checked;
        if (field.type === "multi") value = Array.from(ev.target.selectedOptions).map(o => Number(o.value));
        if (field.type === "number") value = Number(value);
        values[field.key] = value;
        if (field.key === "unit_id" && this.state.editor.kind === "reasons") values.process_id = "";
    }
    closeConfig() { this.state.editor = null; this.state.stageEditor = null; }
    closeStageOverlay(ev) { if (ev.target === ev.currentTarget && !this.state.busy) this.state.stageEditor = null; }
    async saveConfig(nested = false) {
        await this.run(async () => {
            const editor = nested ? this.state.stageEditor : this.state.editor;
            const values = {};
            for (const field of this.fieldsFor(editor.kind)) {
                const value = editor.values[field.key];
                if (field.label.endsWith("*") && (!value || (Array.isArray(value) && !value.length))) throw new Error(`Complete ${field.label.replace(" *", "")}.`);
                values[field.key] = field.type === "multi" ? [[6, 0, value || []]] : field.key.endsWith("_id") ? Number(value) || false : value;
            }
            if (["stages", "transitions"].includes(editor.kind)) values.process_id = this.state.editor.id;
            if (editor.kind === "stages" && values.actor_type !== "users") values.actor_ids = [[6, 0, []]];
            const id = await this.orm.call("incmd.request", "ui_save_configuration", [editor.kind, editor.id || false, values]);
            await this.loadConfiguration(); await this.refreshBootstrap();
            if (nested) this.state.stageEditor = null;
            else { const row = this.configRows.find(r => r.id === id); this.editConfig(row); }
            this.notification.add("Configuración guardada.", { type: "success" });
        });
    }
    get processStages() { return (this.state.config?.stages || []).filter(s => s.process_id[0] === this.state.editor?.id).sort((a,b) => a.sequence - b.sequence || a.id-b.id); }
    get processTransitions() { return (this.state.config?.transitions || []).filter(t => t.process_id[0] === this.state.editor?.id).sort((a,b) => a.sequence - b.sequence || a.id-b.id); }
    editStage(kind, row = null) {
        const values = row ? JSON.parse(JSON.stringify(row)) : this.defaults(kind);
        for (const key of ["process_id", "from_stage_id", "to_stage_id"]) if (Array.isArray(values[key])) values[key] = values[key][0];
        this.state.stageEditor = { kind, id: row?.id || false, values };
    }
    async removeConfig(kind, id) {
        if (!window.confirm("¿Eliminar este registro? Si está publicado o tiene referencias, Odoo impedirá eliminarlo.")) return;
        await this.run(async () => { await this.orm.call("incmd.request", "ui_delete_configuration", [kind, id]); await this.loadConfiguration(); await this.refreshBootstrap(); });
    }
    async moveStage(stage, direction) {
        const ordered = [...this.processStages]; const index = ordered.findIndex(s => s.id === stage.id); const target = index + direction;
        if (target < 0 || target >= ordered.length) return;
        [ordered[index], ordered[target]] = [ordered[target], ordered[index]];
        await this.run(async () => {
            // Una sola escritura en el proceso para ordenar de forma atómica.
            await this.orm.write("incmd.request.process", [this.state.editor.id], { stage_ids: ordered.map((s, i) => [1, s.id, { sequence: (i + 1) * 10 }]) });
            await this.loadConfiguration();
        });
    }
    async publishProcess() {
        if (!window.confirm("¿Publicar esta versión? Después no podrá editarse; los cambios requerirán otra versión.")) return;
        await this.run(async () => {
            await this.orm.call("incmd.request.process", "action_publish", [[this.state.editor.id]]);
            await this.loadConfiguration(); await this.refreshBootstrap();
            this.editConfig(this.configRows.find(p => p.id === this.state.editor.id));
            this.notification.add("Versión publicada. Ya puede asignarla a los motivos.", { type: "success" });
        });
    }
    async newVersion() {
        await this.run(async () => {
            const action = await this.orm.call("incmd.request.process", "action_new_version", [[this.state.editor.id]]);
            await this.loadConfiguration(); this.editConfig(this.configRows.find(p => p.id === action.res_id));
        });
    }
    actorLabel(value) { return { team: "Equipo destinatario", origin_supervisor: "Supervisor de origen", users: "Usuarios específicos" }[value] || value; }
}
registry.category("actions").add("incmd_requests.workspace", RequestsWorkspace);
