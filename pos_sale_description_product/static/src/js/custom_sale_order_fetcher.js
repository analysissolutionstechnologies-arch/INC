/** @odoo-module */

import { registry } from "@web/core/registry";
import { EventBus } from "@odoo/owl"; // Importar EventBus si es necesario

export class CustomSaleOrderFetcher extends EventBus {
    static serviceDependencies = ["orm", "pos"];
    constructor({ orm, pos }) {
        super();
        this.currentPage = 1;
        this.ordersToShow = [];
        this.totalCount = 0;
        this.orm = orm;
        this.pos = pos;
    }

    get lastPage() {
        const nItems = this.totalCount;
        return Math.trunc(nItems / (this.nPerPage + 1)) + 1;
    }

    async fetch() {
        // Show orders from the backend.
        const offset = this.nPerPage + (this.currentPage - 1 - 1) * this.nPerPage;
        const limit = this.nPerPage;
        this.ordersToShow = await this._fetch(limit, offset);

        this.trigger("update");
    }

    async _fetch(limit, offset) {
        const sale_orders = await this._getOrderIdsForCurrentPage(limit, offset);
        this.totalCount = sale_orders.length;
        return sale_orders;
    }

    async _getOrderIdsForCurrentPage(limit, offset) {
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
    
            const orderLineIds = order.order_line;
            
            if (orderLineIds && orderLineIds.length > 0) {
                const orderLines = await this.orm.searchRead(
                    "sale.order.line",
                    [["id", "in", orderLineIds]],
                    ["name", "product_id"]
                );
                debugger
                for (let line of orderLines) {
                    if (line.product_id) {
                        const product = await this.orm.read("product.product", [line.product_id[0]], ["x_studio_es_moto_1"]);
    
                        if (product.length > 0 && product[0].x_studio_es_moto_1) {
                            if (line.name) {
                                lineNames[line.id] = line.name;  
                            }
                        } 
                        if (product.length > 0 && !product[0].x_studio_es_moto_1) {
                            lineNames[line.id] = product.name;  
                        }
                    }
                    line.line_names = lineNames[line.id] || ''; 
                }
            }
    
            order.line_names = lineNames;
        }
    
        this.pos.set_synch("connected");
        return saleOrders;
    }
    
    

    nextPage() {
        if (this.currentPage < this.lastPage) {
            this.currentPage += 1;
            this.fetch();
        }
    }
    prevPage() {
        if (this.currentPage > 1) {
            this.currentPage -= 1;
            this.fetch();
        }
    }

    get(id) {
        return this.ordersToShow;
    }
    setSearchDomain(searchDomain) {
        this.searchDomain = searchDomain;
    }
    setNPerPage(val) {
        this.nPerPage = val;
    }
    setPage(page) {
        this.currentPage = page;
    }
}

export const customSaleOrderFetcherService = {
    dependencies: CustomSaleOrderFetcher.serviceDependencies,
    start(env, deps) {
        return new CustomSaleOrderFetcher(deps);
    },
};

registry.category("services").add("custom_sale_order_fetcher", customSaleOrderFetcherService);
