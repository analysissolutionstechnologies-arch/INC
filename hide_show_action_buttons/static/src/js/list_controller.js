/** @odoo-module **/

import { ListController } from '@web/views/list/list_controller';
import { session } from "@web/session";
import { patch } from "@web/core/utils/patch";
import { onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

patch(ListController.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        onWillStart(async () => {
            const [isExportEnable, isArchiveEnable, isCreateEnable, isDeleteEnable, isDuplicateEnable] = await Promise.all([this._isExportEnable(), this._isArchiveEnable(), this._isCreateEnable(), this._isDeleteEnable(), this._isDuplicateEnable()]);
            if (!isExportEnable) this.isExportEnable = false;
            if (!isArchiveEnable) this.archiveEnabled = false;
            if (!isCreateEnable) this.activeActions.create = false;
            if (!isDeleteEnable) this.activeActions.delete = false;
            if (!isDuplicateEnable) this.activeActions.duplicate = false;
        });
    },
    _isExportEnable: async function () {
        return await this.orm.call('res.users', 'is_export_enable', [session.uid, this.env.searchModel.resModel]);
    },
    _isArchiveEnable: async function () {
        return await this.orm.call('res.users', 'is_archive_enable', [session.uid, this.env.searchModel.resModel]);
    },
    _isCreateEnable: async function () {
        return await this.orm.call('res.users', 'is_create_enable', [session.uid, this.env.searchModel.resModel]);
    },
    _isDeleteEnable: async function () {
        return await this.orm.call('res.users', 'is_delete_enable', [session.uid, this.env.searchModel.resModel]);
    },
    _isDuplicateEnable: async function () {
        return await this.orm.call('res.users', 'is_duplicate_enable', [session.uid, this.env.searchModel.resModel]);
    },
});
