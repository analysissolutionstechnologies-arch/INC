// /** @odoo-module */

// import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
// import { _t } from "@web/core/l10n/translation";
// import { usePos } from "@point_of_sale/app/store/pos_hook";
// import { Order, Orderline } from "@point_of_sale/app/store/models";
// import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";


// export class PosStockWarehouse extends AbstractAwaitablePopup {
//     static template = "bi_pos_multi_warehouse.PosStockWarehouse";
//     static defaultProps = {
//         confirmText: _t("Apply"),
//         cancelText: _t("cancel"),
//         title: "Confirm ?",
//     };

//     setup() {
//         super.setup();
//         this.pos = usePos();
//         this.product = this.props.product;
//         this.result = this.props.result;
//         // Filtra las bodegas que tienen inventario disponible
//         this.locations = (this.result || []).filter(location => {
//             let product_stock = this.pos.db.get_product_by_id(this.product.id);
//             // Verifica si hay inventario en la bodega, ajusta según la lógica de inventario que uses
//             return product_stock && (product_stock.bi_on_hand > 0 || product_stock.virtual_available > 0);
//         });
//         this.location_id = null;
//     }

//     cancel() {
//         this.props.close({ confirmed: false, payload: null });
//     }

//     apply() {
//         let self = this;
//         let product = this.pos.db.get_product_by_id(this.product.id);
//         let rec = this.props.rec;
//         let entered_code = $("#entered_item_qty").val();
//         let list_of_qty = $('.entered_item_qty');
//         let order = this.pos.get_order();
//         let warehouse = this.pos.pos_custom_location;

//         $.each(list_of_qty, function(index, value) {
//             let entered_item_qty =$(value).find('input');
//             let qty_id = parseFloat(entered_item_qty.attr('qty-id'));
//             let loc_id = entered_item_qty.attr('locdbid');
//             let loc_name = entered_item_qty.attr('loc-id');
//             let entered_qty = parseFloat(entered_item_qty.val() || 0);
//             let selectedOrder = self.pos.get_order();

//             if(entered_qty > 0){
//                 if(qty_id >= entered_qty){
//                     if (entered_qty != 0){
//                         if(self.pos.config.stock_qty == 'qty_available'){
//                             product['bi_on_hand'] += entered_qty;
//                         }
//                         else{
//                             product.virtual_available -= entered_qty;
//                         }

//                         var orderline = new Orderline(
//                             { env: self.env },
//                             {
//                                 pos: self.pos,
//                                 order: order,
//                                 product: product,
//                                 stock_location_id:warehouse
//                             }
//                         );

//                         orderline.product = product;
//                         orderline.stock_location_id = loc_id;
//                         orderline.stock_location_name = loc_name;
//                         orderline.set_quantity(entered_qty);
//                         order.add_orderline(orderline);
//                         self.pos.showScreen('ProductScreen');
//                         self.cancel();

//                     }
//                 }
//                 else {
//                     if(self.pos.config.Negative_selling){
//                         if (entered_qty != 0){
//                             var orderline = new Orderline(
//                                 { env: self.env },
//                                 {
//                                     pos: self.pos,
//                                     order: order,
//                                     product: product,
//                                     stock_location_id:warehouse
//                                 }
//                             );
//                             orderline.product = product;
//                             orderline.stock_location_id = loc_id;
//                             orderline.stock_location_name = loc_name;
//                             orderline.set_quantity(entered_qty);
//                             order.add_orderline(orderline);
//                             self.pos.showScreen('ProductScreen');
//                             self.cancel();
//                         }
//                     }
//                     else {
//                         let result = 'This Location has :' + qty_id +' QTY.  You have entered : '+ entered_qty;
//                         self.pos.popup.add(ErrorPopup, {
//                             title: _t('Please enter valid amount of quantity.'),
//                             body: _t(result),
//                         });
//                     }
//                 }
//             }
//         });
//     }
// }

/** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Order, Orderline } from "@point_of_sale/app/store/models";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";

export class PosStockWarehouse extends AbstractAwaitablePopup {
    static template = "bi_pos_multi_warehouse.PosStockWarehouse";
    static defaultProps = {
        confirmText: _t("Apply"),
        cancelText: _t("cancel"),
        title: "Confirm ?",
    };

    setup() {
        super.setup();
        this.pos = usePos();
        this.product = this.props.product;
        this.result = this.props.result;
        // Filtra las bodegas que tienen inventario disponible
        this.locations = (this.result || []).filter(location => {
            let product_stock = this.pos.db.get_product_by_id(this.product.id);
            // Verifica si hay inventario en la bodega
            return product_stock && (product_stock.bi_on_hand > 0 || product_stock.virtual_available > 0);
        });
        this.location_id = null;
    }

    cancel() {
        this.props.close({ confirmed: false, payload: null });
    }

    apply() {
        let self = this;
        let product = this.pos.db.get_product_by_id(this.product.id);
        let list_of_qty = $('.entered_item_qty');
        let order = this.pos.get_order();
        let warehouse = this.pos.pos_custom_location;

        // Validar la lista de precios activa antes de continuar
        const currentPricelist = order.pricelist;
        if (currentPricelist && currentPricelist.id === 3) {
            // Mostrar mensaje en CSS (puedes usar un popup también)
            const warningDiv = document.createElement('div');
            warningDiv.id = 'pos-product-warning';
            warningDiv.textContent = "No se pueden agregar productos con la lista de precios de crédito, modifíquela para continuar.";
            document.body.appendChild(warningDiv);

            // Eliminar el mensaje después de 3 segundos
            setTimeout(() => {
                document.body.removeChild(warningDiv);
            }, 3000);

            // Evitar continuar
            return;
        }

        // Proceder con el flujo normal si la lista de precios es válida
        $.each(list_of_qty, function(index, value) {
            let entered_item_qty = $(value).find('input');
            let qty_id = parseFloat(entered_item_qty.attr('qty-id'));
            let loc_id = entered_item_qty.attr('locdbid');
            let loc_name = entered_item_qty.attr('loc-id');
            let entered_qty = parseFloat(entered_item_qty.val() || 0);

            if (entered_qty > 0) {
                if (qty_id >= entered_qty) {
                    if (entered_qty !== 0) {
                        if (self.pos.config.stock_qty === 'qty_available') {
                            product['bi_on_hand'] += entered_qty;
                        } else {
                            product.virtual_available -= entered_qty;
                        }

                        var orderline = new Orderline(
                            { env: self.env },
                            {
                                pos: self.pos,
                                order: order,
                                product: product,
                                stock_location_id: warehouse,
                            }
                        );

                        orderline.product = product;
                        orderline.stock_location_id = loc_id;
                        orderline.stock_location_name = loc_name;
                        orderline.set_quantity(entered_qty);
                        order.add_orderline(orderline);
                        self.pos.showScreen("ProductScreen");
                        self.cancel();
                    }
                } else {
                    if (self.pos.config.Negative_selling) {
                        if (entered_qty !== 0) {
                            var orderline = new Orderline(
                                { env: self.env },
                                {
                                    pos: self.pos,
                                    order: order,
                                    product: product,
                                    stock_location_id: warehouse,
                                }
                            );
                            orderline.product = product;
                            orderline.stock_location_id = loc_id;
                            orderline.stock_location_name = loc_name;
                            orderline.set_quantity(entered_qty);
                            order.add_orderline(orderline);
                            self.pos.showScreen("ProductScreen");
                            self.cancel();
                        }
                    } else {
                        let result =
                            "This Location has :" +
                            qty_id +
                            " QTY.  You have entered : " +
                            entered_qty;
                        self.pos.popup.add(ErrorPopup, {
                            title: _t("Please enter valid amount of quantity."),
                            body: _t(result),
                        });
                    }
                }
            }
        });
    }
}
