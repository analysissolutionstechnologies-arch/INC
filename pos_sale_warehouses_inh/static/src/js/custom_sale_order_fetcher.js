/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { CustomSaleOrderFetcher } from "@pos_sale_description_product/js/custom_sale_order_fetcher";

patch(CustomSaleOrderFetcher.prototype,{
    async _getOrderIdsForCurrentPage(limit, offset) {
        debugger
        const domain = [["currency_id", "=", this.pos.currency.id]].concat(
            this.searchDomain || []
        );
    
        this.pos.set_synch("connecting");
        const saleOrders = await this.orm.searchRead(
            "sale.order",
            domain,
            [
                "name",
                "partner_id",
                "amount_total",
                "date_order",
                "state",
                "user_id",
                "amount_unpaid",
                "order_line",
            ],
            { offset, limit }
        );

        for (let order of saleOrders) {
            let lineNames = {};        
            let lineWarehouses = {};   
        
            const orderLineIds = order.order_line;
        
            if (orderLineIds && orderLineIds.length > 0) {
                const orderLines = await this.orm.searchRead(
                    "sale.order.line",
                    [["id", "in", orderLineIds]],
                    ["name", "product_id", "warehouses_id"]
                );
        
                for (let line of orderLines) {
                    if (line.product_id) {
                        const products = await this.orm.read(
                            "product.product",
                            [line.product_id[0]],
                            ["x_studio_es_moto_1", "name"]
                        );
        
                        if (products.length > 0) {
                            const product = products[0];
                            if (product.x_studio_es_moto_1) {
                                if (line.name) {
                                    lineNames[line.id] = line.name;
                                }
                            } else {
                                lineNames[line.id] = product.name || "";
                            }
                        }
                    }
                    line.line_names = lineNames[line.id] || '';
        
                    let warehouseName = "";
                    if (
                        line.warehouses_id &&
                        Array.isArray(line.warehouses_id) &&
                        line.warehouses_id.length >= 2
                    ) {
                        warehouseName = line.warehouses_id[1] || "";
                    }
                    lineWarehouses[line.id] = warehouseName;
                }
            }
        
            order.line_names = lineNames;
            order.warehouse_names = lineWarehouses;
        }

        return saleOrders;
    },
})

