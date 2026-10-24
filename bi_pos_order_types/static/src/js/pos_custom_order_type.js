/** @odoo-module */

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    // @Override
    async _processData(loadedData) {
        await super._processData(...arguments);
        let self = this;
        self.pos_custom_order_type = loadedData['pos.order.type'];
        
    },
   
});

patch(Order.prototype, {
    setup() {
        super.setup(...arguments);
        this.order_type_id = this.order_type_id || "";
        this.order_type = this.order_type || "";
        
    },
    set_order_type_id(order_type_id){
        this.order_type_id = order_type_id;
    },
    get_order_type_id(){
        return this.order_type_id;
    },

    set_order_type(order_type){
        this.order_type = order_type;
    },
    get_order_type(){
        return this.order_type;
    },
    
    init_from_JSON(json){
        super.init_from_JSON(...arguments);
        this.order_type_id = json.order_type_id || "";
        this.order_type = json.order_type || "";
    },

    export_as_JSON(){
        const json = super.export_as_JSON(...arguments);
        json.order_type_id = this.get_order_type_id() || "";
        json.order_type = this.order_type || "";
        return json;
    },

    export_for_printing() {
        const json = super.export_for_printing(...arguments);
        json.order_type_id = this.get_order_type_id() || "";
        json.order_type = this.order_type || "";
        return json;
    },
});
