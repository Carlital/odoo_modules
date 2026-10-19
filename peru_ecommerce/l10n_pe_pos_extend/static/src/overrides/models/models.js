/** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { formatDate } from "@web/core/l10n/dates"; //serializeDate

patch(Order.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        this.invoice_date = false;
    },
    //@override
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.invoice_date = this.invoice_date;
        return json;
    },
    //@override
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        if (json.invoice_date) {
            this.invoice_date = json.invoice_date;
        }
    },
    //@override
    export_for_printing(){
        const json = super.export_for_printing(...arguments);
        if (!this.invoice_date){
            this.invoice_date = formatDate(luxon.DateTime.now(), {format:'yyyy/MM/dd'});
        }
        json['invoice_date'] = this.invoice_date;
        json['pe_amount_text'] = this.get_amount_text().toUpperCase();
        json['pe_is_company'] = this.pos.isPeruvianCompany();
        return json
    },
    get_amount_text() {
        return numeroALetras(this.get_total_with_tax(), {
                                          plural: this.pos.currency.currency_unit_label,
                                          singular: this.pos.currency.currency_unit_label,
                                          centPlural: "",
                                          centSingular: ""
                                        })
    },
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        /*if (!this.invoice_date){
            this.invoice_date = formatDate(luxon.DateTime.now());
        }*/
        json.invoice_date = this.invoice_date;
        return json;
    },
    get_pe_doc_type() {
        var partner = this.get_partner();
        var pe_doc_type=partner && (partner.l10n_latam_identification_type_id ? this.pos.l10n_latam_identification_types_by_id[partner.l10n_latam_identification_type_id[0]].l10n_pe_vat_code : "") || "";
        return pe_doc_type;
    },
    get_pe_vat() {
        var partner = this.get_partner();
        var vat=partner ? partner.vat : "";
        return vat;
    }
});
