odoo.define('l10n_uy_edi_pos.models', function (require) {
    "use strict";

var { PosGlobalState, Order, Orderline }  = require('point_of_sale.models');
const Registries = require('point_of_sale.Registries');


const PePosCPEPosGlobalState = (PosGlobalState) => class PePosCPEPosGlobalState extends PosGlobalState {
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.pe_journals = loadedData['account.journal'];
        this.addPeJournals(this.pe_journals);
        
    }
    addPeJournals(pe_journals) {
        return this.db.add_pe_journals(pe_journals);
    }
    async check_pe_sequence(pe_journal_ids) {
        var self = this;
        var pe_move_name = await this.env.services.rpc({
            model: 'account.journal',
            method: 'get_pe_sequence',
            args: [pe_journal_ids],
        }, {
            timeout: 7200,
        })
        .then(function (result) {
            for (var i = 0; i < pe_journal_ids.length; i++) {
                if(result[pe_journal_ids[i]].pe_sequence_number>self.db.get_pe_journal_id_sequence(pe_journal_ids[i])){
                    self.db.set_pe_journal_id_sequence(pe_journal_id, result.pe_sequence_number)
                }
            }

        }).catch(function (error){
            console.log('Failed to get sequence number');
        });
    }
    generate_sync_pe_move_name(pe_journal_id) {
        var journal_id = this.db.get_pe_journals_by_id(pe_journal_id);
        var num = "%0"+journal_id.pe_padding+"d";
        var prefix = journal_id.pe_sequence_prefix || "";
        var increment = this.db.get_pe_journal_id_sequence(pe_journal_id)+1;
        var number = prefix + num.sprintf(parseInt(increment));
        return { 'pe_move_name': number, 'pe_sequence_number':increment};
    }
    get_pe_move_name(pe_journal_id){
        var number = this.generate_sync_pe_move_name(pe_journal_id);
        if (this.db.get_pe_move_names().indexOf(number.pe_move_name)!=-1){
            this.db.set_pe_journal_id_sequence(pe_journal_id, number.pe_sequence_number);
            this.db.add_pe_move_names(number.pe_move_name);
            number = this.get_pe_move_name(pe_journal_id);
        }
        this.db.set_pe_journal_id_sequence(pe_journal_id, number.pe_sequence_number);
        this.db.add_pe_move_names(number.pe_move_name);
        this.check_pe_sequence([pe_journal_id]);
        return number;
    }
}
Registries.Model.extend(PosGlobalState, PePosCPEPosGlobalState);


const PePosCPEOrder = (Order) => class PePosCPEOrder extends Order {
    constructor(obj, options) {
        super(...arguments);
        if (!options.json) {
            this.pe_qr_code = false;
            this.pe_invoice_name = false;
            this.pe_move_name = false;
            this.pe_journal_id = false;
            this.invoice_date = false;
            this.pe_credit_note_code = false;
            this.pe_src_move_name = false;
            if (!this.pe_journal_id){
                this.pos.check_pe_sequence(this.pos.config.pe_default_journal_ids);
            }
        }

    }
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
    }
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json['pe_move_name']=this.get_pe_move_name();
        json['pe_journal_id']=this.get_pe_journal_id();
        return json;
    }
    export_for_printing(){
        var json = super.export_for_printing(...arguments);
        json['pe_move_name']=this.get_pe_move_name();
        json['pe_journal_id']=this.get_pe_journal_id();
        json['pe_qr_string'] = this.get_cpe_qr();
        json['pe_credit_note_code'] = this.pe_credit_note_code;
        json['pe_src_move_name'] = this.pe_src_move_name;
        json['invoice_date'] = this.invoice_date;
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
        return json;
    }
    set_partner(partner){
        super.set_partner(...arguments);
        if (this.pos.config.pe_auto_journal_select){
            this.calculate_pe_document_type();
        }
    }


    set_pe_qr_code(pe_qr_code) {
        this.pe_qr_code = pe_qr_code;
    }
    set_pe_invoice_name(pe_invoice_name) {
        this.pe_invoice_name = pe_invoice_name;
    }
    set_pe_move_name(pe_move_name) {
        this.pe_move_name = pe_move_name;
    }
    get_pe_move_name() {
        return this.pe_move_name;
    }
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
                name+='Electronica';
            }

        }
        this.pe_invoice_name = name;
        this.pe_journal_id = pe_journal_id;
    }
    get_pe_journal_id() {
        return this.pe_journal_id;
    }
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
    }
    get_cpe_type(){
        if (this.pe_journal_id){
            var journal = this.pos.db.get_pe_journals_by_id(this.pe_journal_id);
            return journal.pe_invoice_code;
        }
        else{
            return '';
        }

    }
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
            res.push(this.date_invoice || moment(new Date().getTime()).format('YYYY-MM-DD'));
            res.push(this.get_pe_doc_type() || '-');
            res.push(this.get_vat() || '-');
            qr_string=res.join('|');
        }
        return qr_string;
    }
    
    
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
}
Registries.Model.extend(Order, PePosCPEOrder);


const PePosCPEOrderline = (Orderline) => class PePosCPEOrderline extends Orderline {

    export_for_printing(){
        const json = super.export_for_printing(...arguments);
        json['product_default_code'] = this.get_product().default_code;
        json['full_product_name'] = this.get_full_product_name();
        return json
    }
}
Registries.Model.extend(Orderline, PePosCPEOrderline);
});
