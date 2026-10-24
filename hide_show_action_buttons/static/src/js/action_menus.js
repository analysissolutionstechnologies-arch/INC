/** @odoo-module **/

import { ActionMenus } from "@web/search/action_menus/action_menus";
import { session } from "@web/session";
import { patch } from "@web/core/utils/patch";
import { onWillStart } from "@odoo/owl";

patch(ActionMenus.prototype, {
    setup() {
        super.setup();
        onWillStart(async () => {
            const [isPrintEnable] = await Promise.all([this._isPrintEnable()]);
            if (!isPrintEnable) this.props.items.print = [];
        });
    },
    _isPrintEnable: async function () {
        return await this.orm.call('res.users', 'is_print_enable', [session.uid, this.env.searchModel.resModel]);
    },
});
