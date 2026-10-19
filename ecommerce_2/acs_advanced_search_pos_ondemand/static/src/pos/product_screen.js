/** @odoo-module */

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { unaccent } from "@web/core/utils/strings";

const ACS_ONDEMAND_LOG_PREFIX = "[ACS-ONDEMAND]";
const ACS_ONDEMAND_DEBUG = false;

const DEFAULT_PRODUCT_FIELDS = [
    "name",
    "display_name",
    "default_code",
    "barcode",
    "categ_id",
    "lst_price",
    "standard_price",
    "type",
    "available_in_pos",
    "taxes_id",
    "uom_id",
    "uom_po_id",
    "product_tmpl_id",
    "image_128",
    "tracking",
    "description_sale",
    "pos_categ_ids",
    "standard_name",
];

function normalizeSearchWord(searchWord) {
    return unaccent((searchWord || "").trim(), false).toLowerCase();
}

function getSearchTokens(searchWord) {
    return normalizeSearchWord(searchWord).split(/\s+/).filter(Boolean);
}

function productMatchesSearch(product, normalizedQuery, tokens) {
    if (!normalizedQuery) {
        return true;
    }

    const searchBlob = unaccent(product.searchString || "", false).toLowerCase();
    if (product.exactMatch(normalizedQuery) || searchBlob.includes(normalizedQuery)) {
        return true;
    }

    return tokens.length > 1 && tokens.every((token) => searchBlob.includes(token));
}

function getProductsFromRecords(pos) {
    const records = pos?.data?.records?.["product.product"];
    return records ? Array.from(records.values()) : [];
}

function debugLog(...args) {
    if (ACS_ONDEMAND_DEBUG) {
        console.info(...args);
    }
}

patch(ProductScreen.prototype, {
    get productsToDisplay() {
        const products = super.productsToDisplay;
        const state = this.pos?._acsAdvancedSearchState;
        const activeSearchWord = typeof this.searchWord === "string" ? this.searchWord.trim() : null;
        if (state && activeSearchWord !== null && state.lastQuery !== activeSearchWord) {
            state.lastQuery = activeSearchWord;
        }
        const query = state?.lastQuery || "";
        if (query) {
            const normalizedQuery = normalizeSearchWord(query);
            const tokens = getSearchTokens(query);
            const productModel = this._acsAdvancedSearchGetProductModel();
            const recordProducts = getProductsFromRecords(this.pos);
            const localProducts = productModel?.getAll
                ? productModel.getAll()
                : recordProducts.length
                  ? recordProducts
                  : (this.products || []);
            const globalMatches = localProducts.filter((product) =>
                productMatchesSearch(product, normalizedQuery, tokens)
            );
            const selectedCategory = this.pos?.selectedCategory;
            debugLog(`${ACS_ONDEMAND_LOG_PREFIX} productsToDisplay`, {
                query,
                selectedCategoryId: selectedCategory?.id || null,
                selectedCategoryName: selectedCategory?.name || null,
                count: products?.length || 0,
                globalMatchCount: globalMatches.length,
                sampleIds: (products || []).slice(0, 10).map((product) => product.id),
            });

            // While the user is searching, force global matches so selected POS category
            // does not hide products loaded on demand.
            return globalMatches;
        }
        return products;
    },

    getProductsBySearchWord(searchWord) {
        const query = (searchWord || "").trim();
        const state = this._acsAdvancedSearchGetState();
        state.lastQuery = query;

        const words = normalizeSearchWord(query);
        const tokens = getSearchTokens(query);
        const productModel = this._acsAdvancedSearchGetProductModel();
        const recordProducts = getProductsFromRecords(this.pos);
        const localProducts = productModel?.getAll
            ? productModel.getAll()
            : recordProducts.length
              ? recordProducts
              : (this.products || []);
        const exactMatches = localProducts.filter((product) => product.exactMatch(words));
        const fuzzyMatches = localProducts.filter((product) =>
            productMatchesSearch(product, words, tokens)
        );
        const localMatches = Array.from(new Set([...exactMatches, ...fuzzyMatches]));

        if (query) {
            const selectedCategory = this.pos?.selectedCategory;
            debugLog(
                `${ACS_ONDEMAND_LOG_PREFIX} local search`,
                {
                    query,
                    normalized: words,
                    selectedCategoryId: selectedCategory?.id || null,
                    selectedCategoryName: selectedCategory?.name || null,
                    localPool: localProducts.length,
                    exactMatches: exactMatches.length,
                    fuzzyMatches: fuzzyMatches.length,
                    combinedMatches: localMatches.length,
                }
            );
        }

        if (localMatches.length || !query) {
            return localMatches;
        }

        void this._acsAdvancedSearchLoadMissingProducts(query);
        return localMatches;
    },

    _acsAdvancedSearchGetState() {
        const store = this.pos;

        if (!store._acsAdvancedSearchState) {
            const productModel = this._acsAdvancedSearchGetProductModel();
            const loadedIds = new Set(
                (productModel?.getAll ? productModel.getAll() : []).map((product) => product.id)
            );

            store._acsAdvancedSearchState = {
                loadedIds,
                pending: new Map(),
                lastQuery: "",
            };
        }

        return store._acsAdvancedSearchState;
    },

    _acsAdvancedSearchGetProductModel() {
        return (
            this.pos?.models?.["product.product"] ||
            this.pos?.data?.models?.["product.product"] ||
            this.models?.["product.product"]
        );
    },

    _acsAdvancedSearchGetDataService() {
        return this.pos?.data || this.data;
    },

    _acsAdvancedSearchGetFields() {
        const productModel = this._acsAdvancedSearchGetProductModel();
        const modelFields = Array.isArray(productModel?.fields) ? productModel.fields : [];

        if (modelFields.length) {
            return modelFields;
        }

        return DEFAULT_PRODUCT_FIELDS;
    },

    async _acsAdvancedSearchLoadMissingProducts(searchWord) {
        const state = this._acsAdvancedSearchGetState();
        const normalizedQuery = normalizeSearchWord(searchWord);
        const cacheKey = `global:${normalizedQuery}`;
        state.lastQuery = (searchWord || "").trim();

        debugLog(`${ACS_ONDEMAND_LOG_PREFIX} load-missing start`, {
            query: searchWord,
            normalizedQuery,
            cacheKey,
            alreadyLoadedCount: state.loadedIds.size,
            hasPending: state.pending.has(cacheKey),
        });

        if (state.pending.has(cacheKey)) {
            debugLog(`${ACS_ONDEMAND_LOG_PREFIX} load-missing skip pending`, {
                cacheKey,
            });
            return state.pending.get(cacheKey);
        }

        const promise = this._acsAdvancedSearchFetchAndLoadProducts(searchWord, state)
            .then((records) => {
                debugLog(`${ACS_ONDEMAND_LOG_PREFIX} load-missing done`, {
                    query: searchWord,
                    loadedRecords: records.length,
                });
                this._acsAdvancedSearchDebugPostLoad(searchWord, records);
                if (records.length) {
                    this.render(true);
                }
                return records;
            })
            .catch((error) => {
                console.error("ACS on-demand POS search failed", error);
                return [];
            })
            .finally(() => {
                state.pending.delete(cacheKey);
            });

        state.pending.set(cacheKey, promise);
        return promise;
    },

    async _acsAdvancedSearchFetchAndLoadProducts(searchWord, state) {
        const orm = this.orm || this.env?.services?.orm;
        const dataService = this._acsAdvancedSearchGetDataService();

        if (!orm) {
            console.warn(`${ACS_ONDEMAND_LOG_PREFIX} abort: orm service not available`);
            return [];
        }

        debugLog(`${ACS_ONDEMAND_LOG_PREFIX} rpc call start`, {
            query: searchWord,
            limit: 20,
        });

        const productIdsFromSearch = await orm.call(
            "product.product",
            "acs_pos_ondemand_search_products",
            [searchWord],
            {
            limit: 20,
            context: this.pos?.env?.context || this.env?.context || {},
            }
        );

        debugLog(`${ACS_ONDEMAND_LOG_PREFIX} rpc call done`, {
            query: searchWord,
            idsFromSearch: productIdsFromSearch,
            idsCount: productIdsFromSearch.length,
        });

        const productIds = [...new Set(productIdsFromSearch)].filter(
            (productId) => !state.loadedIds.has(productId)
        );

        debugLog(`${ACS_ONDEMAND_LOG_PREFIX} ids after de-dup and loaded filter`, {
            query: searchWord,
            newIds: productIds,
            newIdsCount: productIds.length,
        });

        if (!productIds.length) {
            return [];
        }

        const fields = this._acsAdvancedSearchGetFields();
        const usedDataService = Boolean(dataService?.searchRead);
        const productRecords = usedDataService
            ? await dataService.searchRead("product.product", [["id", "in", productIds]], fields)
            : await orm.searchRead("product.product", [["id", "in", productIds]], fields);

        debugLog(`${ACS_ONDEMAND_LOG_PREFIX} searchRead done`, {
            query: searchWord,
            recordsCount: productRecords.length,
            recordIds: productRecords.map((record) => record.id),
            usedDataService,
        });

        // dataService.searchRead already integrates records into POS store.
        // Calling loadData again here can break reactive relations in some environments.
        if (!usedDataService) {
            const dataModels = this.pos?.data?.models || dataService?.models;
            if (dataModels?.loadData && productRecords.length) {
                await dataModels.loadData({ "product.product": productRecords });
                debugLog(`${ACS_ONDEMAND_LOG_PREFIX} loadData done`, {
                    query: searchWord,
                    loadedCount: productRecords.length,
                });
            } else {
                console.warn(`${ACS_ONDEMAND_LOG_PREFIX} loadData unavailable or no records`, {
                    hasLoadData: Boolean(dataModels?.loadData),
                    recordsCount: productRecords.length,
                });
            }
        }

        for (const productId of productIds) {
            state.loadedIds.add(productId);
        }

        return productRecords;
    },

    _acsAdvancedSearchDebugPostLoad(searchWord, productRecords) {
        const normalized = normalizeSearchWord(searchWord);
        const selectedCategoryId = this.pos?.selectedCategory?.id || null;
        const productModel = this._acsAdvancedSearchGetProductModel();
        const localProducts = productModel?.getAll
            ? productModel.getAll()
            : getProductsFromRecords(this.pos);

        const loadedById = new Map((productRecords || []).map((record) => [record.id, record]));
        const loadedProductsInStore = localProducts.filter((product) => loadedById.has(product.id));

        const matchesInStore = loadedProductsInStore.filter((product) => {
            const searchBlob = unaccent(product.searchString || "", false).toLowerCase();
            const name = unaccent(product.display_name || product.name || "", false).toLowerCase();
            const defaultCode = (product.default_code || "").toLowerCase();
            const barcode = (product.barcode || "").toLowerCase();
            return (
                searchBlob.includes(normalized) ||
                name.includes(normalized) ||
                defaultCode.includes(normalized) ||
                barcode.includes(normalized)
            );
        });

        const inSelectedCategory = selectedCategoryId
            ? loadedProductsInStore.filter((product) =>
                Array.isArray(product.pos_categ_ids) && product.pos_categ_ids.includes(selectedCategoryId)
            )
            : loadedProductsInStore;

        debugLog(`${ACS_ONDEMAND_LOG_PREFIX} post-load diagnostics`, {
            query: searchWord,
            normalized,
            selectedCategoryId,
            requestedRecordIds: (productRecords || []).map((record) => record.id),
            loadedProductsInStoreCount: loadedProductsInStore.length,
            matchesInStoreCount: matchesInStore.length,
            inSelectedCategoryCount: inSelectedCategory.length,
            sample: loadedProductsInStore.slice(0, 10).map((product) => ({
                id: product.id,
                name: product.display_name || product.name || "",
                default_code: product.default_code || "",
                barcode: product.barcode || "",
                pos_categ_ids: product.pos_categ_ids || [],
                hasSearchString: Boolean(product.searchString),
            })),
        });
    },
});
