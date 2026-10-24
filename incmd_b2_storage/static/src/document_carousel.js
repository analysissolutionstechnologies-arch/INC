/** @odoo-module **/
import { Component, onWillStart, onWillUpdateProps, useState } from '@odoo/owl';
import { registry } from '@web/core/registry';
import { useService } from '@web/core/utils/hooks';

export class DocumentCarousel extends Component {
    static template = 'incmd_b2_storage.DocumentCarousel';
    static props = ['*'];
    setup() {
        this.orm = useService('orm');
        this.state = useState({ documents: [], index: 0, loading: false, error: false, odtText: "", odtLoading: false, odtError: false });
        this.orderId = this.props.record.resId;
        this.requestNumber = 0;
        onWillStart(() => this.load(this.orderId));
        onWillUpdateProps((props) => {
            if (props.record.resId !== this.orderId) {
                this.orderId = props.record.resId;
                return this.load(this.orderId);
            }
        });
    }
    async load(id = this.orderId) {
        const request = ++this.requestNumber;
        this.state.loading = true;
        this.state.error = false;
        try {
            const documents = id ? await this.orm.call(this.modelName, 'b2_get_carousel_documents', [[id]]) : [];
            if (request === this.requestNumber) {
                this.state.documents = documents;
                this.state.index = 0;
                await this.loadOdt();
            }
        } catch (error) {
            if (request === this.requestNumber) {
                this.state.error = true;
                this.state.documents = [];
            }
        } finally {
            if (request === this.requestNumber) this.state.loading = false;
        }
    }
    get modelName() { return 'sale.order'; }
    get current() { return this.state.documents[this.state.index]; }
    get isImage() { return (this.current?.mimetype || '').startsWith('image/'); }
    get isVideo() {
        return (this.current?.mimetype || '').startsWith('video/') || /\.(mp4|webm|mov|m4v|ogv|avi|mkv|vid)$/i.test(this.current?.name || '');
    }
    get isPdf() { return this.current?.mimetype === "application/pdf" || /\.pdf$/i.test(this.current?.name || ""); }
    get isOdt() { return /\.odt$/i.test(this.current?.name || ""); }
    async loadOdt() {
        const doc = this.current;
        this.state.odtText = ""; this.state.odtError = false;
        this.state.odtLoading = this.isOdt;
        if (!this.isOdt) return;
        try {
            const value = await this.orm.call("ir.attachment", "b2_get_odt_preview", [[doc.id]]);
            if (this.current?.id === doc.id) this.state.odtText = value;
        } catch (error) {
            if (this.current?.id === doc.id) this.state.odtError = true;
        } finally {
            if (this.current?.id === doc.id) this.state.odtLoading = false;
        }
    }
    get source() {
        return `/web/image/ir.attachment/${this.current.id}/datas?width=256&height=256&unique=${encodeURIComponent(this.current.write_date || '')}`;
    }
    get original() { return `/web/content/ir.attachment/${this.current.id}/datas?download=false`; }
    previous() {
        const count = this.state.documents.length;
        if (count) { this.state.index = (this.state.index + count - 1) % count; this.loadOdt(); }
    }
    next() {
        const count = this.state.documents.length;
        if (count) { this.state.index = (this.state.index + 1) % count; this.loadOdt(); }
    }
    refresh() { return this.load(); }
}
registry.category('view_widgets').add('b2_document_carousel', { component: DocumentCarousel });

export class ProjectDocumentCarousel extends DocumentCarousel {
    static template = 'incmd_b2_storage.ProjectDocumentCarousel';
    get modelName() { return 'project.task'; }
    get source() {
        return `/web/image/ir.attachment/${this.current.id}/datas?width=1200&height=1200&unique=${encodeURIComponent(this.current.write_date || '')}`;
    }
}
registry.category('view_widgets').add('b2_project_document_carousel', { component: ProjectDocumentCarousel });
