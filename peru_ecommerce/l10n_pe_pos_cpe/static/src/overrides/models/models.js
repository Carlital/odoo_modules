/** @odoo-module */

import { Order, Orderline, Payment } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { formatDate } from "@web/core/l10n/dates";

// New orders are now associated with the current table, if any.
patch(Order.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        this.pe_qr_code = false;
        this.pe_invoice_name = false;
        this.pe_move_name = false;
        this.pe_journal_id = false;
        this.invoice_date = false;
        this.pe_credit_note_code = false;
        this.pe_src_move_name = false;
        /*if (!this.pe_journal_id){
            this.pos.check_pe_sequence(this.pos.config.pe_default_journal_ids);
        }*/
    },
    //@override
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json['pe_move_name']=this.get_pe_move_name();
        json['pe_journal_id']=this.get_pe_journal_id();
        return json;
    },
    //@override
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        if (json.pe_move_name){
            this.set_pe_move_name(json.pe_move_name);
        }
        if (json.pe_journal_id){
            this.set_pe_journal_id(json.pe_journal_id);
        }
        if(json.invoice_date){
            this.invoice_date = json.invoice_date;
        }
        if (json.pe_src_move_name){
            this.pe_src_move_name = json.pe_src_move_name;
        }
    },
    //@override
    export_for_printing(){
        const json = super.export_for_printing(...arguments);

        json['pe_move_name']=this.get_pe_move_name();
        json['pe_journal_id']=this.get_pe_journal_id();
        json['pe_qr_string'] = this.get_cpe_qr();
        json['pe_credit_note_code'] = this.pe_credit_note_code;
        json['pe_src_move_name'] = this.pe_src_move_name;
        json['invoice_date'] = this.invoice_date;
        json['pe_invoice_name'] = this.pe_invoice_name;
        var pe_qr_code = false;
        if (this.get_cpe_type()!=""){
            var qr = new QRious();
            qr.set({
              level: 'Q',
              padding: 5,
              size: 150,
              value: this.get_cpe_qr()
            });
            pe_qr_code = qr.toDataURL();
        }
        json['pe_qr_code'] = pe_qr_code;
        console.log(json);
        return json;
    },
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        /*if (!this.invoice_date){
            this.invoice_date = formatDate(luxon.DateTime.now());
        }*/
        json['invoice_date'] = this.invoice_date;
        json['pe_move_name']=this.get_pe_move_name();
        json['pe_journal_id']=this.get_pe_journal_id();
        json['pe_credit_note_code'] = this.pe_credit_note_code;
        json['pe_src_move_name'] = this.pe_src_move_name;
        return json;
    },
    set_partner(partner){
        super.set_partner(...arguments);
        if (this.pos.config.pe_auto_journal_select){
            this.calculate_pe_document_type();
        }
    },
    set_pe_qr_code(pe_qr_code) {
        this.pe_qr_code = pe_qr_code;
    },
    set_pe_invoice_name(pe_invoice_name) {
        this.pe_invoice_name = pe_invoice_name;
    },
    set_pe_move_name(pe_move_name) {
        this.pe_move_name = pe_move_name;
    },
    get_pe_move_name() {
        return this.pe_move_name;
    },
    set_pe_journal_id(pe_journal_id) {
        var journal = this.pos.db.get_pe_journals_by_id(pe_journal_id);
        var name = '';
        if (pe_journal_id && journal){
            if (journal.pe_invoice_code == '01'){
                name+='Factura ';
            }
            if (journal.pe_invoice_code == '03'){
                name+='Boleta de venta ';
            }
            if (journal.pe_invoice_code == '07'){
                name+='Nota de crédito ';
            }
            if (journal.pe_invoice_code == '08'){
                name+='Nota de débito ';
            }
            if (journal.pe_is_cpe){
                name+='Electrónica';
            }

        }
        this.pe_invoice_name = name;
        this.pe_journal_id = pe_journal_id;
    },
    get_pe_journal_id() {
        return this.pe_journal_id;
    },


    calculate_pe_document_type() {
        if (!this.get_partner()){
            this.set_pe_journal_id(false);
            return ;
        }
        if (this.get_pe_doc_type() == '6'){
            this.set_pe_journal_id(this.pos.db.get_pe_journals_by_pe_invoice_code('01'));
        }
        else{
            this.set_pe_journal_id(this.pos.db.get_pe_journals_by_pe_invoice_code('03'));
        }
    },
    get_cpe_type(){
        if (this.pe_journal_id){
            var journal = this.pos.db.get_pe_journals_by_id(this.pe_journal_id);
            return journal.pe_invoice_code;
        }
        else{
            return '';
        }

    },
    get_cpe_qr(){
        var qr_string = "";
        if (this.get_cpe_type()!=""){
            var res=[]
            res.push(this.pos.company.vat);
            res.push(this.get_cpe_type() || ' ');
            res.push(this.get_pe_move_name() && this.get_pe_move_name().split("-")[0]  || ' ');
            res.push(this.get_pe_move_name() && this.get_pe_move_name().split("-")[1]  || ' ');
            res.push(this.get_total_tax() || 0.0);
            res.push(this.get_total_with_tax() || 0.0);
            res.push(this.date_invoice || formatDate(luxon.DateTime.now({format:'yyyy/MM/dd'})));
            res.push(this.get_pe_doc_type() || '-');
            res.push(this.get_pe_vat() || '-');
            qr_string=res.join('|');
        }
        return qr_string;
    },
    get_valid_pe_journal_ids() {
        var journal_ids = [];
        var journal = this.pos.db.get_pe_journals_by_id(this.pe_journal_id);
        if (journal){
            if(journal.pe_invoice_code=='07'){
                return journal_ids;
            }
        }
        for (var i = 0; i < this.pos.config.pe_journal_ids.length; i++) {
            var journal = this.pos.db.get_pe_journals_by_id(this.pos.config.pe_journal_ids[i]);
            if (journal.pe_invoice_code == '01'){
                journal_ids.push(journal);
            }
            if (journal.pe_invoice_code == '03'){
                journal_ids.push(journal);
            }
        }
        return journal_ids;
    }
});

patch(Orderline.prototype, {
    export_for_printing(){
        const json = super.export_for_printing(...arguments);
        json['product_default_code'] = this.get_product().default_code;
        json['full_product_name'] = this.get_full_product_name();
        return json
    }
});