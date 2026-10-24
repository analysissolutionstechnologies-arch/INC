/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { Order, Orderline } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { PosStockWarehouse } from "@bi_pos_multi_warehouse/js/WarehouseStock";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";



patch(PosStore.prototype, {
    async _processData(loadedData) {
        await super._processData(loadedData);
        let self = this;
        self.prod_with_quant = loadedData['prod_with_quant'] || [];
        self.pos_custom_location = loadedData['pos_custom_location'] || [];
        self.loc_by_id = loadedData['loc_by_id'] || [];
        self.locations = loadedData['locations'] || [];
    },

    async addProductToCurrentOrder(product, options = {}) {
        let self = this;
        const prod = product;
        let order = this.get_order();
        let location = this.config.warehouse_ids;
        let partner_id = order.get_partner();
        let lines = order.get_orderlines();
        let warehouse = this.pos_custom_location;
        let session = this.config.stock_qty;
        
        if (this.config.default_location_src_id) {
            let config_loc = parseInt(this.config.default_location_src_id[0]);
            let loc_qty = this.prod_with_quant[product.id] || {};
    
            if (loc_qty && config_loc) {
                let config_loc_qty = loc_qty[config_loc] || 0;
                let rec = 0;
    
                if (product.type == 'product' && this.config.display_stock) {
                    let products = order.calculate_prod_qty();
                    if (config_loc_qty > 0 || this.config.Negative_selling || this.config.stock_qty) {
                        await this.env.services.orm.call(
                            'stock.quant',
                            'warehouse_qty',
                            [partner_id, warehouse, product.id, session],
                        ).then(function (output) {
                            if (lines.length > 0) {
                                for (let i in output) {
                                    $.each(output[i], function (k, v) {
                                        if (k == 'location') {
                                            if (products[v]) {
                                                let found = $.grep(products[v], function (q) {
                                                    if (q['name'] == product.display_name) {
                                                        output[i]['quantity'] = output[i]['quantity'] - q['qty'];
                                                    }
                                                });
                                            }
                                        }
                                    });
                                }
                                rec = output;
                            } else {
                                rec = output;
                            }
                        });
                        order.set_loaded_qty(rec);
                        await this.popup.add(PosStockWarehouse, {
                            'product': product,
                            'rec': rec,
                        });
                    } else {
                        self.popup.add(ErrorPopup, {
                            title: _t('Out of Stock'),
                            body: _t('Quantity is not available'),
                        });
                    }
                } else {
                    super.addProductToCurrentOrder(product, options = {});
                }
            } else {
                console.error(`No se encontró información de cantidad para la ubicación de configuración: ${this.config.default_location_src_id[1]}`);
                self.popup.add(ErrorPopup, {
                    title: _t('Error'),
                    body: _t(`No se encontró información de cantidad para la ubicación de configuración: ${this.config.default_location_src_id[1]}`),
                });
            }
        } else {
            super.addProductToCurrentOrder(product, options = {});
        }
    }
    
    

});

patch(Order.prototype,{
    setup() {
        super.setup(...arguments);
        this.order_products = this.order_products || {};
        this.prd_qty = this.prd_qty || {};
        this.loaded_qty = this.loaded_qty || {};

    },
    set_loaded_qty(qty){
        this.loaded_qty = qty;
    },
    export_as_JSON() {
			var self = this;
			var loaded = super.export_as_JSON(...arguments);
			loaded.loaded_qty = self.loaded_qty || {};
			loaded.order_products = self.order_products || {};
			return loaded;
		},

    init_from_JSON(json){
        super.init_from_JSON(...arguments);
        this.order_products = json.order_products || {};
        this.prd_qty = json.prd_qty || {};
        this.loaded_qty = json.loaded_qty || {};
    },

    get_display_product_qty(prd){
        var self = this;
        var products = {};
        var order = this.pos.get_order();
        var display_qty = 0;
        if(order){
            var orderlines = order.get_orderlines();
            if(orderlines.length > 0 && self.pos.config.default_location_src_id){
                orderlines.forEach(function (line) {
                    if(line.product['id'] == prd.id){
                        display_qty += line.get_quantity()
                    }
                });
            }
        }
        return display_qty
    },

    calculate_prod_qty() {
        var self = this;
        var products = {};
        var order = this.pos.get_order();
        if(order){
            var orderlines = order.get_orderlines();
            if(order.prd_qty  == undefined){
                order.prd_qty = {};
            }
            if(order.order_products  == undefined){
                order.order_products = {};
            }
            if(orderlines.length > 0 && self.pos.config.default_location_src_id){
                orderlines.forEach(function (line) {
                    var prod = line.product;

                    order.order_products[prod.id] = self.pos.prod_with_quant[prod.id];
                    var loc = line.stock_location_name;

                    if(prod.type == 'product'){
                        if(products[loc] == undefined){
                            products[loc] =  [{
                                'loc' :loc,
                                'line' : line.id,
                                'name': prod.display_name,
                                'id':prod.id,
                                'prod_qty_available' : prod.qty_available,
                                'qty' :parseFloat(line.quantity)
                            }];
                            prod.qty_available = prod.qty_available - line.quantity
                        }
                        else{
                            let found = $.grep(products[loc], function(v) {
                                return v.id === prod.id;
                            });
                            if(found){
                                products[loc].forEach(function (val) {
                                    if(val['id'] == prod.id){
                                        if(val['line'] == line.id){
                                            val['qty'] = parseFloat(line.quantity);
                                        }else{
                                            val['qty'] += parseFloat(line.quantity);
                                        }
                                    }
                                });
                            }
                            if(found.length == 0){
                                products[loc].push({
                                    'loc' :loc,
                                    'line' : line.id,
                                    'name': prod.display_name,
                                    'id':prod.id,
                                    'prod_qty_available' : prod.qty_available,
                                    'qty' :parseFloat(line.quantity)
                                })
                                prod.qty_available = prod.qty_available - line.quantity
                            }
                        }
                    }
                });
            }
            order.prd_qty = products;

        }

        return products;
    },
    
    async pay() {
        var self = this;
        let order = this.pos.get_order();
        let products_data = order.calculate_prod_qty()
        let lines = order.get_orderlines();
        let pos_config = self.pos.config;
        let allow_order = pos_config.Negative_selling;
        let call_super = true;
        if (order.get_order_type() === 'Tipo de Pedido' || !order.get_order_type()) {
            this.pos.popup.add(ErrorPopup, {
                title: _t('Campo Requerido'),
                body: _t('Debe seleccionar un Tipo de Pedido antes de proceder con el pago.'),
            });
            return;
        }        
        if(pos_config.display_stock){
            let prod_used_qty = {};
            $.each(lines, function( i, line ){
                let locations = self.pos.locations;
                let prd = line.product;
                let loc_onhand = JSON.parse(prd.quant_text);
                locations = locations.filter(function(item){
                    return item.warehouse_id[1] == line.stock_location_name
                })

                if (prd.type == 'product'){
                    let loc_onhand = JSON.parse(prd.quant_text);
                    $.each(loc_onhand, function( k, v ){
                        locations.forEach(function (location) {
                            if(location.id == k){
                                var final_data = products_data[location.warehouse_id[1]]
                                final_data.forEach(function (data) {
                                    if(location.warehouse_id[1] == data.loc && data['id'] == prd.id){
                                        debugger
                                        data['qty'] = line.quantity;
                                        data['prod_qty_available'] = line.get_quantity();
                                    }
                                })
                            }
                        })
                    })

                }
            });
            $.each(products_data, function( product ){
                var found = products_data[product]
                 found.forEach(function (data) {
                    if (allow_order == false && data['qty'] > data['prod_qty_available']){
                        call_super = false;
                        self.pos.popup.add(ErrorPopup, {
                            title: _t('Denegar orden'),
                            body: _t("Denegar orden" + "(" + data['name'] + ")" + " está agotado."),
                        });
                    }
                })


            });
        }
        if(call_super){
            super.pay();
        }
    }

});

patch(Orderline.prototype,{
    setup() {
        super.setup(...arguments);
        this.stock_location_id = this.stock_location_id || false;
        this.stock_location_name = this.stock_location_name || false;
    },
    set_stock_location_name(stock_location_name){
        this.stock_location_name = stock_location_name
        this.trigger('change',this);
    },
    get_stock_location_name(){
        return this.stock_location_name;
    },

    getDisplayData() {
        return {
            ...super.getDisplayData(),
            location_name:this.get_stock_location_name(),
        };
    },
    set_stock_location_id(stock_location_id){
        this.stock_location_id = stock_location_id
        this.trigger('change',this);
    },
    get_stock_location_id(){
        return this.stock_location_id;
    },
    can_be_merged_with(orderline) {
          if (orderline.get_stock_location_name() !== this.get_stock_location_name()) {
            return false;
        } else {
            return super.can_be_merged_with(...arguments);;
        }

    },
    export_for_printing(){
        var json = super.export_for_printing(...arguments);
        json.is_location_warehouse = this.get_stock_location_name();
        return json;
    },
    export_as_JSON(){

        var json = super.export_as_JSON(...arguments);
        json.stock_location_name = this.get_stock_location_name();
        return json;
    },
    init_from_JSON(json){
        super.init_from_JSON(...arguments);
        this.stock_location_name = json.stock_location_name;

    }
});






