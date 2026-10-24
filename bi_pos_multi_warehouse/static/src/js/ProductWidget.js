///** @odoo-module */
//
//import { ProductsWidget } from "@point_of_sale/app/screens/product_screen/product_list/product_list";
//import { patch } from "@web/core/utils/patch";
//import { usePos } from "@point_of_sale/app/store/pos_hook";
//
//
//patch(ProductsWidget.prototype,{
//
//    setup() {
//        super.setup();
//        this.pos = usePos();
//    },
//    get productsToDisplay() {
//        let self = this;
//        let prods = super.productsToDisplay;
//        let order = self.pos.get_order();
//        if (self.pos.config.display_stock){
//            let prod_ids = [];
//            $.each(prods, function( i, prd ){
//                prod_ids.push(prd.id)
//            });
//            let locations = self.pos.locations;
//            if(self.pos.config.stock_qty == 'qty_available'){
//                $.each(prods, function( i, prd ){
//                    // prd['qty_available'] = 0;
//                    let qty_value=0
//                    let loc_onhand = JSON.parse(prd.quant_text);
//                    let warehouse = self.pos.pos_custom_location;
//                    locations.forEach(function (location) {
//                        for (const [key, value] of Object.entries(loc_onhand)) {
//                              if(location.id == key){
//                                qty_value=qty_value+value[0]
//                            }
//                        }
//                    })
//                    if(prd['bi_on_hand']>0){
//                        prd['bi_on_hand'] = order.get_display_product_qty(prd)
//                        prd['qty_available'] = qty_value - prd['bi_on_hand']
//                    }
//                    else{
//                        if(order){
//                            var reserved_qty = order.get_display_product_qty(prd);
//                            prd['qty_available'] = qty_value - reserved_qty;
//                        }
//                        else{
//                            prd['qty_available']=qty_value
//                        }
//                    }
//                });
//            }
//            else{
//                $.each(prods, function( i, prd ){
//                    let loc_available = JSON.parse(prd.quant_text);
//                    prd['virtual_available'] = 0;
//                    let total = 0;
//                    locations.forEach(function (location) {
//                        $.each(loc_available, function( k, v ){
//                            if(location.id == k){
//                                total += v[0];
//                            }
//                        })
//                    });
//                    let out_qty = prd['outgoing_qty']
//                    let final_data = total - out_qty;
//                    prd['virtual_available'] = final_data;
//                });
//            }
//        }
//
//        if (this.searchWord !== '') {
//            return this.pos.db.search_product_in_category(
//                this.selectedCategoryId,
//                this.searchWord
//            );
//        } else {
//            return this.pos.db.get_product_by_category(this.selectedCategoryId);
//        }
//    }
//
//});

/** @odoo-module */

import { ProductsWidget } from "@point_of_sale/app/screens/product_screen/product_list/product_list";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";

patch(ProductsWidget.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
    },

    get productsToDisplay() {
        let self = this;
        let prods = super.productsToDisplay;
        let order = self.pos.get_order();

        if (self.pos.config.display_stock) {
            let prod_ids = [];
            $.each(prods, function (i, prd) {
                prod_ids.push(prd.id);
            });

            // 🔴 Filtrar solo ubicaciones internas y excluir otras (incluyendo tránsito)
            let locations = self.pos.locations.filter(location => {
                return location.usage === "internal"; // Solo almacenes internos
            });

            console.log("Ubicaciones filtradas (solo internas):", locations); // 🔍 Debugging

            if (self.pos.config.stock_qty === "qty_available") {
                $.each(prods, function (i, prd) {
                    let qty_value = 0;
                    let loc_onhand = JSON.parse(prd.quant_text) || {};

                    locations.forEach(function (location) {
                        if (loc_onhand[location.id]) {
                            qty_value += loc_onhand[location.id][0];
                        }
                    });

                    if (prd["bi_on_hand"] > 0) {
                        prd["bi_on_hand"] = order.get_display_product_qty(prd);
                        prd["qty_available"] = qty_value - prd["bi_on_hand"];
                    } else {
                        let reserved_qty = order ? order.get_display_product_qty(prd) : 0;
                        prd["qty_available"] = qty_value - reserved_qty;
                    }
                });
            } else {
                $.each(prods, function (i, prd) {
                    let loc_available = JSON.parse(prd.quant_text) || {};
                    let total = 0;

                    locations.forEach(function (location) {
                        if (loc_available[location.id]) {
                            total += loc_available[location.id][0];
                        }
                    });

                    let out_qty = prd["outgoing_qty"] || 0;
                    prd["virtual_available"] = total - out_qty;
                });
            }
        }

        if (this.searchWord !== "") {
            return this.pos.db.search_product_in_category(
                this.selectedCategoryId,
                this.searchWord
            );
        } else {
            return this.pos.db.get_product_by_category(this.selectedCategoryId);
        }
    }
});






