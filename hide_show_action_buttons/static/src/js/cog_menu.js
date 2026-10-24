/** @odoo-module **/

import { CogMenu } from "@web/search/cog_menu/cog_menu";
import { session } from "@web/session";
import { patch } from "@web/core/utils/patch";

patch(CogMenu.prototype, {
    async _registryItems() {
        let [isImportEnable, isExportEnable, registryItems] = await Promise.all([this._isImportEnable(),  this._isExportEnable(), super._registryItems()]);
        if (!isImportEnable) registryItems = registryItems.filter(item => item.key !== 'ImportRecords');
        if (!isExportEnable) registryItems = registryItems.filter(item => item.key !== 'ExportAll');
        return registryItems;
    },
    async _isImportEnable() {
        return await this.orm.call('res.users', 'is_import_enable', [session.uid, this.env.searchModel.resModel]);
    },
    async _isExportEnable () {
        return await this.orm.call('res.users', 'is_export_enable', [session.uid, this.env.searchModel.resModel]);
    },
});
        