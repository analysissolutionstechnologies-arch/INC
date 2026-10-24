/** @odoo-module **/
import { BinaryField, binaryField } from '@web/views/fields/binary/binary_field';
import { registry } from '@web/core/registry';

export class DocumentPreview extends BinaryField {
    static template = 'incmd_b2_storage.DocumentPreview';
    get documentName() { return this.props.record.data[this.props.fileNameField] || ''; }
    get previewKind() {
        const name = this.documentName.toLowerCase();
        if (/\.(jpg|jpeg|png)$/.test(name)) return 'image';
        if (/\.pdf$/.test(name)) return 'pdf';
        return 'document';
    }
    get fullImageSource() {
        const id = this.props.record.resId;
        if (!id || this.props.record.dirty) return this.previewSource;
        return `/web/content/ir.attachment/${id}/datas?download=false`;
    }
    get previewSource() {
        const value = this.props.record.data[this.props.name];
        // Saved binary fields may contain only a human-readable size.
        if (!value) return false;
        if (typeof value === 'string' && value.length >= 32 && /^[A-Za-z0-9+/=\r\n]+$/.test(value)) {
            const mime = this.previewKind === 'pdf' ? 'application/pdf' : (/\.png$/i.test(this.documentName) ? 'image/png' : 'image/jpeg');
            return `data:${mime};base64,${value}`;
        }
        const id = this.props.record.resId;
        if (!id) return false;
        // Odoo serves this through its normal attachment permission checks.
        // Explicit dimensions let the storage adapter use the remote thumbnail.
        const version = encodeURIComponent(this.props.record.data.write_date || '');
        if (this.previewKind === 'image') {
            return `/web/image/ir.attachment/${id}/datas?width=512&height=512&unique=${version}`;
        }
        if (this.previewKind === 'pdf') {
            return `/web/content/ir.attachment/${id}/datas?download=false&unique=${version}`;
        }
        return false;
    }
}
registry.category('fields').add('b2_document_preview', { ...binaryField, component: DocumentPreview });
