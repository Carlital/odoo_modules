
import { Many2XAutocomplete } from "@web/views/fields/relational_utils";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { RPCError } from "@web/core/network/rpc";

patch(Many2XAutocomplete.prototype, {
    search(name) {
        if(this.props.resModel == 'product.product' || this.props.resModel == 'product.template'){
            return this.orm.call(this.props.resModel, "name_search", [], {
                name: 'rgEBAb?!gY@#@93GR$@NRrAxN@?pEAs8Y3ipXfh4',
                operator: "ilike",
                args: this.props.getDomain(),
                limit: 1,
                context: this.props.context,
            });
        }else{
            return super.search(name);
        }
        
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
        if(this.props.resModel == 'product.product' || this.props.resModel == 'product.template'){
            records.length = 1;
        }
        if (!this.props.noSearchMore && records.length > 0) {
            options.push({
                label: this.SearchMoreButtonLabel,
                action: this.onSearchMore.bind(this, request),
                classList: "o_m2o_dropdown_option o_m2o_dropdown_option_search_more",
            });
        }

        
        if(this.props.resModel == 'product.product' || this.props.resModel == 'product.template'){
            var canCreateEdit = false;
            this.props.quickCreate = false;
        }else{
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
    }

})

