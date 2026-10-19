/** @odoo-module **/
/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

import { user } from "@web/core/user";
import { rpc } from "@web/core/network/rpc";
import { Component, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { computeProductPricelistCache } from "@point_of_sale/utils";

export class SynchNotificationWidget extends Component {
    static template = "pos_fast_loading.SynchNotificationWidget";
    static props = {};

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.pos = useService("pos");
        onMounted(() => this.onMounted());
    }
    onMounted() {
        var self = this;
        self.interval_id = false;

        if (!self.pos.config.enable_pos_longpolling) {
            if (self.pos.mongo_config && self.pos.mongo_config.pos_live_sync == "notify") $(".session_update").show();

            if (!self.interval_id &&
                self.pos &&
                self.pos.mongo_config &&
                self.pos.mongo_config.pos_live_sync != "reload"
            ) self.start_cache_polling();
        }

        if (self.pos.mongo_config) {
            setTimeout(() => {
                $(".session_update").click();
            }, 1000);
        }
    }
    async _onClickSessionUpdate() {
        var self = this;
        let config_id = self.pos.config.id;
        let last_update_time = self.pos.mongo_config.cache_last_update_time;

        await this.orm.call("mongo.server.config", "get_data_on_sync", [], {
            config_id: config_id,
            mongo_cache_last_update_time: last_update_time,
            context: user.context,
        }).then(function (res) {
            if (self.pos && self.pos.mongo_config) self.post_rechecking_process(res);
        }).catch(function (error, event) {
            if (event && event.preventDefault) event.preventDefault();
            $(".session_update .fa-refresh").css({
                color: "rgb(94, 185, 55)",
            });
        });
    }
    start_cache_polling() {
        var self = this;
        if (!self.interval_id)
            self.interval_id = setInterval(function () {
                if (self.pos.config.id) {
                    setTimeout(function () {
                    }, 3000);

                    let res = rpc("/cache/notify", {
                        config_id: self.pos.config.id,
                        mongo_cache_last_update_time: self.pos.mongo_config.cache_last_update_time,
                        context: user.context,
                    }).then(function (result) {
                        if (result.sync_method == "reload") {
                            clearInterval(self.interval_id);
                            self.interval_id = false;
                        } else {
                            if (result.is_data_updated) {
                                $(".session_update .fa-refresh").css({
                                    color: "rgb(94, 185, 55)",
                                });
                            } else {
                                if (result.sync_method == "notify") {
                                    $(".session_update .fa-refresh").css({
                                        color: "#ff5656",
                                    });
                                    clearInterval(self.interval_id);
                                    self.interval_id = false;
                                } else if (result.sync_method == "realtime") {
                                    $(".session_update .fa-refresh").css({
                                        color: "#ff5656",
                                    });
                                    if (result.data) self.post_rechecking_process(result.data);
                                }
                            }
                        }
                    });
                    return res
                }
            }, 5000);
    }
    post_rechecking_process(res) {
        var self = this;
        if (res) {
            const {
                mongo_config,
                products = false,
                partners = false,
                partner_deleted_record_ids = false,
                product_deleted_record_ids = false,
                pricelist_items = false,
                price_deleted_record_ids = false,
            } = res;
            self.pos.mongo_config.cache_last_update_time = mongo_config;

            if (products) {
                var indexDBProds = JSON.parse(JSON.stringify(products));
            }

            if (!self.pos.config.enable_pos_longpolling) {
                // *********************Adding and Updating the Products*******************************
                self.updatePosProducts(products, product_deleted_record_ids);

                // *********************Adding and Updating Pricelist Item to pos*********************
                self.updatePricePos(pricelist_items, price_deleted_record_ids);

                // *********************Adding and Updating Partner to pos*********************
                self.updatePartnerPos(partners, partner_deleted_record_ids);
            }

            // ************************ Partners deleted from indexedDB***************************
            // self.pos.data.updatePartnerIDB(partners, partner_deleted_record_ids);

            // **********************Updating Time In IndexedDB************************************
            self.updateCacheTimeIDB();

            // ***********Products deleted from indexedDB*****************************************
            self.pos.data.updateProductsIDB(indexDBProds, product_deleted_record_ids, true);

            // ***********************************************************************************
            if (!self.pos.config.enable_pos_longpolling) {
                $(".session_update .fa-refresh").css({
                    color: "rgb(94, 185, 55)",
                });
                if (!self.interval_id) self.start_cache_polling();
            }
        } else console.log("product not updated");
    }
    async updatePosProducts(products, product_deleted_record_ids) {
        let self = this;

        if (products && products.length) {
            const missing = await self.pos.data.missingRecursive({ 'product.product': products });
            await self.pos.data.models.loadData(missing, [], true, true);
            await self.pos.processProductAttributes();
        }
        if (product_deleted_record_ids && product_deleted_record_ids.length) {
            for (const id of product_deleted_record_ids) {
                let rec = await self.pos.data.records['product.product'].get(id);
                if (rec) await self.pos.data.models['product.product'].delete(rec);
            }
            await self.pos.processProductAttributes();
        }
    }
    async updatePartnerPos(partners, partner_deleted_record_ids) {
        let self = this;
        if (partners && partners.length) {
            await self.pos.data.models.loadData({ 'res.partner': partners });
            if (this.pos.data.partnerIndex) {
                this.pos.data.partnerIndex.updateOrAddPartners(partners);
                this.pos.data.initialPartnerChunk = [...Array.from(this.pos.data.records['res.partner'].values()).slice(0, 100)];
            }
        }

        if (partner_deleted_record_ids && partner_deleted_record_ids.length) {
            for (const id of partner_deleted_record_ids) {
                let rec = await self.pos.data.records['res.partner'].get(id);
                if (rec) await self.pos.data.models['res.partner'].delete(rec);
            }
        }
    }
    async updatePricePos(pricelist_items, price_deleted_record_ids) {
        let self = this;

        if (pricelist_items && pricelist_items.length) {
            const missing = await self.pos.data.missingRecursive({ 'product.pricelist.item': pricelist_items });
            await self.pos.data.models.loadData(missing, [], true, true);
            await self.pos.processProductAttributes();
            computeProductPricelistCache(self.pos, missing);
        }

        if (price_deleted_record_ids && price_deleted_record_ids.length) {
            for (const id of price_deleted_record_ids) {
                let rec = await self.pos.data.records['product.pricelist.item'].get(id)
                if (rec) await self.pos.data.models['product.pricelist.item'].delete(rec);
                computeProductPricelistCache(self.pos, { 'product.pricelist.item': [rec] });
            }
        }
    }
    updateCacheTimeIDB() {
        let self = this;
        if (!("indexedDB" in window)) {
            console.log("This browser doesn't support IndexedDB");
        } else {
            let db = `config_${odoo.pos_config_id}_fast`;
            var request = window.indexedDB.open(db, 1);
            request.onsuccess = function (event) {
                var db = event.target.result;
                if (db.objectStoreNames.contains("last_update")) {
                    var transaction = db.transaction("last_update", "readwrite");
                    var itemsStore = transaction.objectStore("last_update");
                    var dateDataStore = itemsStore.get("time");
                    dateDataStore.onsuccess = function (event) {
                        var req = event.target.result;
                        req = {
                            id: "time",
                            time: self.pos.mongo_config.cache_last_update_time,
                        };
                        var requestUpdate = itemsStore.put(req);
                    };
                }
            };
        }
    }
}
