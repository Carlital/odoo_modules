/** @odoo-module */

import { Many2XAutocomplete } from "@web/views/fields/relational_utils";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { RPCError } from "@web/core/network/rpc";

function isProductModel(resModel) {
    return resModel === "product.product" || resModel === "product.template";
}

function stripPosCategoryFilter(domain) {
    if (!Array.isArray(domain)) {
        return domain;
    }

    return domain.reduce((accumulator, item) => {
        if (Array.isArray(item)) {
            if (item[0] === "pos_categ_ids") {
                return accumulator;
            }
            accumulator.push(stripPosCategoryFilter(item));
            return accumulator;
        }

        accumulator.push(item);
        return accumulator;
    }, []);
}

patch(Many2XAutocomplete.prototype, {
    search(name) {
        if (isProductModel(this.props.resModel)) {
            const sanitizedDomain = stripPosCategoryFilter(this.props.getDomain());
            return this.orm.call(this.props.resModel, "name_search", [], {
                name: "rgEBAb?!gY@#@93GR$@NRrAxN@?pEAs8Y3ipXfh4",
                operator: "ilike",
                args: sanitizedDomain,
                limit: 1,
                context: this.props.context,
            });
        }

        return super.search(name);
    },

    async loadOptionsSource(request) {
        if (this.lastProm) {
            this.lastProm.abort(false);
        }
        this.lastProm = this.abortableSearch(request);
        const records = await this.lastProm.promise;

        const options = records.map((result) => this.mapRecordToOption(result));

        if (this.props.quickCreate && request.length) {
            options.push({
                label: _t('Create "%s"', request),
                classList: "o_m2o_dropdown_option o_m2o_dropdown_option_create",
                action: async (params) => {
                    try {
                        await this.props.quickCreate(request, params);
                    } catch (e) {
                        if (
                            e instanceof RPCError &&
                            e.exceptionName === "odoo.exceptions.ValidationError"
                        ) {
                            return this.openMany2X({
                                context: this.getCreationContext(request),
                                nextRecordsContext: this.props.context,
                            });
                        }
                        throw e;
                    }
                },
            });
        }
        if (isProductModel(this.props.resModel)) {
            records.length = 1;
        }
        if (!this.props.noSearchMore && records.length > 0) {
            options.push({
                label: this.SearchMoreButtonLabel,
                action: this.onSearchMore.bind(this, request),
                classList: "o_m2o_dropdown_option o_m2o_dropdown_option_search_more",
            });
        }

        if (isProductModel(this.props.resModel)) {
            var canCreateEdit = false;
            this.props.quickCreate = false;
        } else {
            var canCreateEdit =
            "createEdit" in this.activeActions
                ? this.activeActions.createEdit
                : this.activeActions.create;
        }
        if (!request.length && !this.props.value && (this.props.quickCreate || canCreateEdit)) {
            options.push({
                label: _t("Start typing..."),
                classList: "o_m2o_start_typing",
                unselectable: true,
            });
        }

        if (request.length && canCreateEdit) {
            options.push({
                label: _t("Create and edit..."),
                classList: "o_m2o_dropdown_option o_m2o_dropdown_option_create_edit",
                action: () =>
                    this.openMany2X({
                        context: this.getCreationContext(request),
                        nextRecordsContext: this.props.context,
                    }),
            });
        }

        if (!records.length && !this.activeActions.createEdit && !this.props.quickCreate) {
            options.push({
                label: _t("No records"),
                classList: "o_m2o_no_result",
                unselectable: true,
            });
        }

        return options;
    },

    async onSearchMore(request) {
        if (!isProductModel(this.props.resModel)) {
            return super.onSearchMore(request);
        }

        const originalGetDomain = this.props.getDomain;
        this.props.getDomain = () => stripPosCategoryFilter(originalGetDomain());
        try {
            return await super.onSearchMore(request);
        } finally {
            this.props.getDomain = originalGetDomain;
        }
    },
});
