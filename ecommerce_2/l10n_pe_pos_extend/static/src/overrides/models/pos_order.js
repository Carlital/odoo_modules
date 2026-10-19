import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";
import { deserializeDate, formatDate, formatDateTime, serializeDate } from "@web/core/l10n/dates";
const { DateTime } = luxon;

patch(PosOrder.prototype, {
    //@override
    setup(vals) {
        super.setup(...arguments);
        this.invoice_date = false;
        this.pe_invoice_date = vals.pe_invoice_date || false;
    },
    //@override
    export_for_printing(baseUrl, headerData){
        const json = super.export_for_printing(...arguments);
        if (!this.invoice_date){
            this.invoice_date = serializeDate(DateTime.now());
        }
        if (!this.pe_invoice_date){
            this.pe_invoice_date = serializeDate(DateTime.now());
        }
        json['invoice_date'] = deserializeDate(this.invoice_date);
        json['pe_invoice_date'] = deserializeDate(this.pe_invoice_date);
        json['pe_amount_text'] = this.get_amount_text().toUpperCase();
        json['pe_is_company'] = this.company.country_id.code == "PE";
        return json;
    },
    get_amount_text() {
        return numeroALetras(Math.abs(this.get_total_with_tax()), {
                                          plural: this.currency.currency_unit_label,
                                          singular: this.currency.currency_unit_label,
                                          centPlural: "",
                                          centSingular: ""
                                        })
    },
    get_pe_doc_type() {
        var partner = this.get_partner();
        var pe_doc_type=partner && partner.l10n_latam_identification_type_id?.l10n_pe_vat_code || "";
        return pe_doc_type;
    },
    get_pe_vat() {
        var partner = this.get_partner();
        var vat=partner ? partner.vat : "";
        return vat;
    }
});
