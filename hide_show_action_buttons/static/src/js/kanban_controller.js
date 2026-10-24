/** @odoo-module **/

import { KanbanController } from "@web/views/kanban/kanban_controller";
import { session } from "@web/session";
import { patch } from "@web/core/utils/patch";
import { onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

patch(KanbanController.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        onWillStart(async () => {
            const [isCreateEnable] = await Promise.all([this._isCreateEnable()]);
            if (!isCreateEnable) this.archInfo.activeActions.create = false;
        });
    },
    _isCreateEnable: async function () {
        return await this.orm.call('res.users', 'is_create_enable', [session.uid, this.env.searchModel.resModel]);
    },
});
