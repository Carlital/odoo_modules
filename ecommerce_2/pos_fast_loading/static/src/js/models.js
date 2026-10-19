/** @odoo-module **/
/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

import { patch } from "@web/core/utils/patch";
import { registry } from "@web/core/registry";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { PosData } from "@point_of_sale/app/models/data_service";
import { createRelatedModels } from "@point_of_sale/app/models/related_models";
import { PartnerList } from "@point_of_sale/app/screens/partner_list/partner_list";
import { unaccent } from "@web/core/utils/strings";

patch(PosData.prototype, {
    async loadInitialData() {
        let context = await this.update_required_context();
        let res = await this.orm.call("pos.session", "load_data", [
            odoo.pos_session_id,
            PosData.modelToLoad,
        ], { context: context });
        return res;
    },
    update_required_context() {
        return new Promise((resolve, reject) => {
            const context = {};
            const dbName = `config_${odoo.pos_config_id}_fast`;
            const request = window.indexedDB.open(dbName, 1);

            request.onsuccess = async (event) => {
                const db = event.target.result;
                if (db.objectStoreNames.contains("last_update")) {
                    const res = await getRecordsIndexedDB(db, "last_update");
                    context["sync_from_mongo"] = true;
                    context["is_indexed_updated"] = res;
                    resolve(context);
                }
            };

            request.onerror = () => reject();

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                db.createObjectStore("last_update", { keyPath: "id" });
                db.createObjectStore("products", { keyPath: "id" });
                db.createObjectStore("partners", { keyPath: "id" });
            };
        });
    },
    async initData() {
        const modelClasses = {};
        const relations = {};
        const fields = {};
        const data = {};
        const response = await this.loadInitialData();

        for (const [model, values] of Object.entries(response)) {
            if (!window.indexedDB) {
                console.log("This browser doesn't support IndexedDB");
                relations[model] = values.relations;
                fields[model] = values.fields;
                data[model] = values.data;
            } else if (["product.product", "res.partner"].includes(model)) {
                relations[model] = values.relations;
                fields[model] = values.fields;
            } else {
                relations[model] = values.relations;
                fields[model] = values.fields;
                data[model] = values.data;
            }
        }

        for (const posModel of registry.category("pos_available_models").getAll()) {
            const pythonModel = posModel.pythonModel;
            const extraFields = posModel.extraFields || {};
            modelClasses[pythonModel] = posModel;
            relations[pythonModel] = { ...relations[pythonModel], ...extraFields };
        }

        const { models, records, indexedRecords } = createRelatedModels(
            relations,
            modelClasses,
            this.opts
        );

        this.records = records;
        this.indexedRecords = indexedRecords;
        this.fields = fields;
        this.relations = relations;
        this.models = models;

        const order = data["pos.order"] || [];
        const orderlines = data["pos.order.line"] || [];

        delete data["pos.order"];
        delete data["pos.order.line"];

        this.models.loadData(data, this.modelToLoad);
        this.models.loadData({ "pos.order": order, "pos.order.line": orderlines });

        const dbData = await this.loadIndexedDBData();
        this.loadedIndexedDBProducts = dbData ? dbData["product.product"] : [];
        this.network.loading = false;

        if (data['mongo.server.config']?.length) {
            this.mongo_config_id = data['mongo.server.config'][0]['id'];
            this.mongo_config_limit = data['mongo.server.config'][0]['limit'];
        }

        if (window.indexedDB) {
            const prods = response['product.product'];
            const partners = response['res.partner'];
            await this.custom_product_load(prods.data, prods.raw_count);
            await this.custom_partner_load(partners.data);
        }
    },

    async custom_product_load(products, count) {
        const self = this;
        const dbName = `config_${odoo.pos_config_id}_fast`;
        const deepCopiedProducts = products?.length ? JSON.parse(JSON.stringify(products)) : [];

        if (count || products.length) {
            self.models.loadData({ "product.product": products });
            self.loadRemProductsFast();
        }

        const request = window.indexedDB.open(dbName, 1);
        request.onsuccess = async function (event) {
            const db = event.target.result;
            if (!count && !products.length) {
                const res = await getRecordsIndexedDB(db, 'products');
                self.loadProductsInChunks(res, self.mongo_config_limit).then(() => {
                    self.products_load_indexdb = true;
                    console.log("Product loaded through IndexedDB...");
                }).catch((err) => {
                    console.error("Product loading failed", err);
                });
            } else if (db.objectStoreNames.contains("products")) {
                await self.updateIDBRecords(db, "products", deepCopiedProducts, []);
            }
        };
    },
    async loadRemProductsFast() {
        let res, page = 1;
        const self = this;
        const company_id = self.models['pos.config'].get(odoo.pos_config_id).company_id.id;
        let offset = self.mongo_config_limit;
        do {
            res = await self.orm.call("mongo.server.config", "load_rem_product", [0, page, company_id, odoo.pos_session_id, offset]);

            const products = res['products'] || [];
            if (products.length) {
                const deepCopiedProducts = JSON.parse(JSON.stringify(products));
                await self.updateProductsIDB(deepCopiedProducts, []);
                const missing = await self.missingRecursive({ 'product.product': products });
                await new Promise((resolve) => {
                    requestIdleCallback(() => {
                        self.models.loadData(missing, [], true, true);
                        resolve();
                    });
                });
            }
            page += 1;
            offset += self.mongo_config_limit;
        } while (res['raw_count']);

        self.products_load_default = true;
        console.log("Product loaded through default...");
    },
    async loadProductsInChunks(products, chunkSize = 1000) {
        const self = this;
        for (let i = 0; i < products.length; i += chunkSize) {
            const chunk = products.slice(i, i + chunkSize);
            const missing = await self.missingRecursive({ 'product.product': chunk });

            await new Promise((resolve) => {
                requestIdleCallback(() => {
                    self.models.loadData(missing, [], true, true);
                    resolve();
                });
            });
        }
        console.log("Product loading through IndexDB in chunks completed.");
    },

    custom_partner_load(partners) {
        const self = this;
        if(self.mongo_config_id){
            const isCompressedStringArray = Array.isArray(partners) && typeof partners[0] === 'string';
            if (isCompressedStringArray && partners.length > 0) {
                console.log('Starting fast partner loading with multiple compressed chunks...');
                setTimeout(() => {
                    requestIdleCallback(() => {
                        try {
                            console.time("Total Decompression Time");
                            let allPartners = [];
    
                            for (const base64Str of partners) {
                                const binaryStr = atob(base64Str);
                                const compressedData = new Uint8Array(binaryStr.length);
                                for (let i = 0; i < binaryStr.length; i++) {
                                    compressedData[i] = binaryStr.charCodeAt(i);
                                }
                                const decompressed = pako.inflate(compressedData, { to: 'string' });
                                const partnerChunk = Object.values(JSON.parse(decompressed));
                                allPartners = allPartners.concat(partnerChunk);
                            }
                            console.timeEnd("Total Decompression Time");
                            for (const partner of allPartners) {
                                partner.searchString = computeSearchString(partner);
                            }
                            this.partnerIndex = new PartnerIndex(allPartners);
                            const initialChunk = allPartners.slice(0, 1000);
                            self.models.loadData({ "res.partner": initialChunk });
                            console.log(`Loaded initial ${initialChunk.length} partners for fast UI.`);
    
                            const remaining = allPartners.slice(1000);
                            self.loadPartnersInChunks(remaining, 5000);
                        } catch (e) {
                            console.error("Failed to decompress/load multiple partner chunks", e);
                        }
                    });
                }, 0);
    
                // Store last update timestamp
                const dbName = `config_${odoo.pos_config_id}_fast`;
                const dateRequest = indexedDB.open(dbName, 1);
                dateRequest.onupgradeneeded = function (event) {
                    const db = event.target.result;
                    if (!db.objectStoreNames.contains("last_update")) {
                        db.createObjectStore("last_update", { keyPath: "id" });
                    }
                };
                dateRequest.onsuccess = function (event) {
                    const dateDB = event.target.result;
                    try {
                        const transaction = dateDB.transaction("last_update", "readwrite");
                        const store = transaction.objectStore("last_update");
                        const data = {
                            id: "time",
                            time: self.records['mongo.server.config'][0]?.cache_last_update_time,
                        };
                        store.put(data);
                    } catch (e) {
                        console.log("Exception storing last update timestamp", e);
                    }
                };
            } else {
                self.models.loadData({ "res.partner": partners });
                console.warn("No valid compressed partner data to load.");
            }
        }else{
            self.models.loadData({ "res.partner": partners });
        }
    },
    async loadPartnersInChunks(partners, chunkSize = 5000) {
        const self = this;

        for (let i = 0; i < partners.length; i += chunkSize) {
            const chunk = partners.slice(i, i + chunkSize);
            const missing = await self.missingRecursive({ 'res.partner': chunk });

            await new Promise((resolve) => {
                requestIdleCallback(() => {
                    self.models.loadData(missing, [], true, true);
                    console.log(`Loaded chunk ${i / chunkSize + 1} (${chunk.length} partners)`);
                    resolve();
                });
            });
        }

        console.log("All background partner chunks loaded.");
    },

    async updateProductsIDB(products, product_deleted_record_ids) {
        const self = this;
        const dbName = `config_${odoo.pos_config_id}_fast`;

        if ((!products || !products.length) && (!product_deleted_record_ids || !product_deleted_record_ids.length)) return;

        if (!("indexedDB" in window)) {
            console.log("This browser doesn't support IndexedDB");
            return;
        }

        const request = window.indexedDB.open(dbName, 1);
        request.onsuccess = async function (event) {
            const db = event.target.result;
            await self.updateIDBRecords(db, "products", products, product_deleted_record_ids);
        };
    },
    async updatePartnerIDB(partners, partner_deleted_record_ids) {
        let self = this;

        if (
            (partners && partners.length) ||
            (partner_deleted_record_ids && partner_deleted_record_ids.length)
        ) {
            if (!("indexedDB" in window)) {
                console.log("This browser doesn't support IndexedDB");
            } else {
                var request = window.indexedDB.open("Partners", 1);
                request.onsuccess = function (event) {
                    var db = event.target.result;
                    var transaction = db.transaction("partners", "readwrite");
                    var itemsStore = transaction.objectStore("partners");
                    if (partners && partners.length) {
                        partners.forEach(function (item) {
                            var data_store = itemsStore.get(item.id);
                            data_store.onsuccess = function (event) {
                                var data = event.target.result;
                                data = item;
                                const updateRequest = itemsStore.put(data);
                                updateRequest.onsuccess = (event) => {
                                    console.log(event)
                                  };

                                  updateRequest.onerror = (event) => {
                                    console.log(event)
                                  };
                                
                            };
                        });
                    }
                    if (
                        partner_deleted_record_ids &&
                        partner_deleted_record_ids.length
                    ) {
                        partner_deleted_record_ids.forEach(function (id) {
                            var data_store = itemsStore.get(id);
                            data_store.onsuccess = function (event) {
                                var data = event.target.result;
                                var requestUpdate = itemsStore.delete(id);
                            };
                        });
                    }
                };
            }
        }
    },
    async updateIDBRecords(db, storeName, products = [], deleteIds = []) {
        const transaction = db.transaction(storeName, "readwrite");
        const store = transaction.objectStore(storeName);

        for (const item of products) {
            const cleaned = { ...item };
            delete cleaned.pos;
            delete cleaned.env;
            delete cleaned.applicablePricelistItems;
            store.put(cleaned);
        }

        for (const id of deleteIds) {
            store.delete(id);
        }
    },
});

patch(PosStore.prototype, {
    async processServerData() {
        let self = this;
        await super.processServerData(...arguments);
        this.mongo_config = this.data.models['mongo.server.config'].get(this.data.mongo_config_id);

        const intervalId = setInterval(async function () {
            if (!self.data.products_load_default) {
                if (self.data.products_load_indexdb) {
                    self.searchProductWord = 'a';
                    self.searchProductWord = '';
                    await self.processProductAttributes();
                    clearInterval(intervalId);
                }
            }
        }, 3000);
    },
    async processProductAttributes() {
        const productIds = new Set();
        const productTmplIds = new Set();
        const productByTmplId = {};

        for (const product of this.models["product.product"].getAll()) {
            if (product.product_template_variant_value_ids.length > 0) {
                productTmplIds.add(product.raw.product_tmpl_id);
                productIds.add(product.id);

                if (!productByTmplId[product.raw.product_tmpl_id]) {
                    productByTmplId[product.raw.product_tmpl_id] = [];
                }

                productByTmplId[product.raw.product_tmpl_id].push(product);
            }
        }

        if (productIds.size > 0) {
            await this.data.searchRead("product.product", [
                "&",
                ["id", "not in", [...productIds]],
                ["product_tmpl_id", "in", [...productTmplIds]],
            ]);
        }

        //updated this part
        // for (const product of this.models["product.product"].filter(
        //     (p) => !productIds.has(p.id) && p.product_template_variant_value_ids.length > 0
        // )) {
        //     productByTmplId[product.raw.product_tmpl_id].push(product);
        // }

        for (const product of this.models["product.product"].filter(
            (p) => !productIds.has(p.id) && p.product_template_variant_value_ids.length > 0
        )) {
            if (!productByTmplId[product.raw.product_tmpl_id]) {
                productByTmplId[product.raw.product_tmpl_id] = [];
            }
            productByTmplId[product.raw.product_tmpl_id].push(product);
        }
        
        for (const products of Object.values(productByTmplId)) {
            const nbrProduct = products.length;

            for (let i = 0; i < nbrProduct - 1; i++) {
                products[i].available_in_pos = false;
                this.mainProductVariant[products[i].id] = products[nbrProduct - 1];
            }
        }
    },
});

function getRecordsIndexedDB(db, store) {
    return new Promise((resolve) => {
        const transaction = db.transaction(store, "readonly");
        const objectStore = transaction.objectStore(store);
        const request = objectStore.getAll();
        request.onsuccess = () => resolve(request.result);
    });
}

patch(PartnerList.prototype, {
    getPartners() {
        if(this.pos.data.partnerIndex){
            const query = (this.state.query || "").trim();
            const partnerId = this.props.partner?.id;
            
            if (!query) {
                let partners = Array.from(this.pos.data.records["res.partner"].values()).slice(0, 1000);
                if(partnerId){
                    const already = partners.some(p => p.id === partnerId);
                    if(!already){
                        const partner = this.pos.data.models['res.partner'].get(partnerId);
                        if(partner) partners.push(partner);
                    }
                }
                partners = partners.toSorted((a, b) =>
                    this.props.partner?.id === a.id
                        ? -1
                        : this.props.partner?.id === b.id
                        ? 1
                        : (a.name || "").localeCompare(b.name || "")
                );
                return partners;
            }
            const searchWord = unaccent(query, false).toLowerCase();
            const numberString = searchWord.replace(/[+\s()-]/g, "");
            const isSearchWordNumber = /^[0-9]+$/.test(numberString);
            return this.pos.data.partnerIndex.searchPartners(searchWord, numberString, isSearchWordNumber, partnerId);
        }else{
            return super.getPartners();
        }
    },
});

class PartnerIndex {
    constructor(partners) {
        this.partnerMap = {};
        this.searchIndex = '';
        this._lines = new Map();
        this.allPartners = partners;
        this._buildSearchIndex(partners);
    }
    _buildSearchIndex(partners) {
        for (const p of partners) {
            this._preparePartner(p);
        }
        this._rebuildSearchIndex();
    }
    _preparePartner(p) {
        if (!p.searchString) {
            p.searchString = computeSearchString(p);
        }
        p._normalizedSearchString = unaccent(p.searchString).toLowerCase();
        this.partnerMap[p.id] = p;
        const line = `[${p.id}] ${p._normalizedSearchString}`;
        this._lines.set(p.id, line);
    }
    _rebuildSearchIndex() {
        this.searchIndex = [...this._lines.values()].join('\n');
    }
    updateOrAddPartners(partners) {
        let changed = false;
        for (const p of partners) {
            const oldLine = this._lines.get(p.id);
            this._preparePartner(p);
            const newLine = `[${p.id}] ${p._normalizedSearchString}`;
            if (oldLine !== newLine) {
                this._lines.set(p.id, newLine);
                changed = true;
            }
        }
        if (changed) this._rebuildSearchIndex();
    }
    getExactMatches(searchWord) {
        const result = [];
        const target = searchWord.toLowerCase();
        for (const partner of Object.values(this.partnerMap)) {
            if ((partner.barcode || '').toLowerCase() === target) {
                result.push(partner);
            }
        }
        return result;
    }
    searchPartners(searchWord, numberString, isSearchWordNumber, preferredPartnerId, limit = 100) {
        const result = [];
        const term = isSearchWordNumber ? numberString : searchWord;
        const regex = new RegExp(`\\[(\\d+)](?=.*${term})`, 'g');
        let match;

        while ((match = regex.exec(this.searchIndex)) !== null) {
            const id = parseInt(match[1]);
            const partner = this.partnerMap[id];
            if (!partner) continue;

            const target = isSearchWordNumber
                ? partner._normalizedSearchString.replace(/[+\s()-]/g, "")
                : partner._normalizedSearchString;

            if (target.includes(term)) {
                result.push(partner);
                if (result.length >= limit) break;
            }
        }

        // Sort by preferred partner first, then name
        return result.sort((a, b) => {
            if (a.id === preferredPartnerId) return -1;
            if (b.id === preferredPartnerId) return 1;
            return (a.name || '').localeCompare(b.name || '');
        });
    }
}

function computeSearchString(partner) {
    const fields = [
        "name",
        "barcode",
        "phone",
        "mobile",
        "email",
        "vat",
        "parent_name",
        "contact_address",
    ];
    return fields
        .map((field) => {
            const val = partner[field];
            return (field === "phone" || field === "mobile") && val
                ? val.replace(/[+\s()-]/g, "")
                : val || "";
        })
        .filter(Boolean)
        .join(" ");
}
