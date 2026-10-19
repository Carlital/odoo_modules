/** @odoo-module */

import { PosDB } from "@point_of_sale/app/store/db";
import { patch } from "@web/core/utils/patch";

/*patch(PosDB, 'l10n_pe_pos_cpe.db', {

})*/

patch(PosDB.prototype, {
    /*constructor(options){
        this.pe_journal_by_id={};
        this.pe_journal_by_pe_invoice_code={};
        super.constructor(...arguments);
    },*/
    add_pe_journals(journals) {
        if (journals==undefined){
            return;
        }
        if(!journals instanceof Array){
            journals = [journals];
        }
        this.pe_journal_by_id={};
        this.pe_journal_by_pe_invoice_code={};
        for(var i = 0, len = journals.length; i < len; i++){
            var journal = journals[i];
            this.pe_journal_by_id[journal.id] = journal;
            if (journal.pe_invoice_code == '01' || journal.pe_invoice_code == '03'){
                this.pe_journal_by_pe_invoice_code[journal.pe_invoice_code] = journal;
            }
        }
    },
    get_pe_journals_by_pe_invoice_code(pe_invoice_code) {
        return this.pe_journal_by_pe_invoice_code[pe_invoice_code] ? this.pe_journal_by_pe_invoice_code[pe_invoice_code].id: false;
    },
    get_pe_journals_refund_by_pe_invoice_code(pe_invoice_code) {
        var pe_credit_note_id = this.pe_journal_by_pe_invoice_code[pe_invoice_code] ? this.pe_journal_by_pe_invoice_code[pe_invoice_code].pe_credit_note_id: false;
        return pe_credit_note_id ? pe_credit_note_id[0]: false;
    },
    get_pe_journals_by_id(pe_journal_id) {
        return this.pe_journal_by_id[pe_journal_id] || false;
    },
    add_pe_move_names(pe_move_name){
        if (pe_move_name){
            var pe_move_names= this.load('pe_move_names') || [];
            pe_move_names.push(pe_move_name);
            this.save('pe_move_names', pe_move_names || null);
        }
    },
    get_pe_move_names(){
        return this.load('pe_move_names') || [];
    },
    set_pe_journal_id_sequence(pe_journal_id, number_increment){
        var pe_sequences= this.load('pe_sequences') || {};
        pe_sequences[pe_journal_id]=number_increment;
        this.save('pe_sequences', pe_sequences || null);
    },
    get_pe_journal_id_sequence(pe_journal_id){
        var pe_sequences= this.load('pe_sequences') || {};
        if (pe_sequences[pe_journal_id]){
            if (this.pe_journal_by_id[pe_journal_id].pe_sequence_number>pe_sequences[pe_journal_id]) {
                return  this.pe_journal_by_id[pe_journal_id].pe_sequence_number;
            }
            else {
                return pe_sequences[pe_journal_id];
            }
        }
        else{
            return  this.pe_journal_by_id[pe_journal_id].pe_sequence_number;
        }
    },
});