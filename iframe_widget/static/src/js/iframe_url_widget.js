/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class IframeUrlWidget extends Component {
    static template = "iframe_widget.IframeUrlWidget";
    static props = {
        ...standardFieldProps,
    };

    get iframeUrl() {
        return this.props.record.data[this.props.name] || '';
    }

    get showIframe() {
        const url = this.iframeUrl;
        return url && url.trim() !== '';
    }
}

registry.category("fields").add("iframe_url", {
    component: IframeUrlWidget,
});
