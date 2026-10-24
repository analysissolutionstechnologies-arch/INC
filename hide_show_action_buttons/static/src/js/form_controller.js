/** @odoo-module **/

import { FormController } from '@web/views/form/form_controller';
import { session } from "@web/session";
import { patch } from "@web/core/utils/patch";
import { onWillStart } from "@odoo/owl";

patch(FormController.prototype, {
    archiveEnable: true,
    setup() {
        super.setup();
        onWillStart(async () => {
            const [isArchiveEnable, isDeleteEnable, isDuplicateEnable, isCreateEnable, isEditEnable] = await Promise.all([this._isArchiveEnable(), this._isDeleteEnable(), this._isDuplicateEnable(), this._isCreateEnable(), this._isEditEnable()]);
            this.archiveEnable = isArchiveEnable;
            if (!isDeleteEnable) this.archInfo.activeActions.delete = false;
            if (!isDuplicateEnable) this.archInfo.activeActions.duplicate = false;
            if (!isCreateEnable) {
                this.canCreate = false;
                this.archInfo.activeActions.create = false;
            }
            if (!isEditEnable) {
                this.canEdit = false;
                this.archInfo.activeActions.edit = false;
            }
        });
    },
    _isArchiveEnable: async function () {
        return await this.orm.call('res.users', 'is_archive_enable', [session.uid, this.env.searchModel.resModel]);
    },
    _isDeleteEnable: async function () {
        return await this.orm.call('res.users', 'is_delete_enable', [session.uid, this.env.searchModel.resModel]);
    },
    _isDuplicateEnable: async function () {
        return await this.orm.call('res.users', 'is_duplicate_enable', [session.uid, this.env.searchModel.resModel]);
    },
    _isCreateEnable: async function () {
        return await this.orm.call('res.users', 'is_create_enable', [session.uid, this.env.searchModel.resModel]);
    },
    _isEditEnable: async function () {
        return await this.orm.call('res.users', 'is_edit_enable', [session.uid, this.env.searchModel.resModel]);
    },
    get archiveEnabled() {
        if (!this.archiveEnable) return false;
        return super.archiveEnabled;
    }
});
