/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { formatDate } from "@web/core/l10n/dates";

patch(PosStore.prototype, {
    //@override
    async setup() {
        await super.setup(...arguments);
        this.pe_move_names = [];
        this.pe_sequences = {};
    },
    // @Override
    async processServerData() {
        await super.processServerData(...arguments);
        if (this.isPeruvianCompany()) {
            this["account.journal"] = this.data["account.journal"];
        }
    },
    async check_pe_sequence(pe_journal_ids) {
        var self = this;
        try {
            var result = await this.data.call("account.journal", "get_pe_sequence", [pe_journal_ids]);
            for (var i = 0; i < pe_journal_ids.length; i++) {
                if(result[pe_journal_ids[i]].pe_sequence_number>self.get_pe_journal_id_sequence(pe_journal_ids[i])){
                    self.set_pe_journal_id_sequence(pe_journal_id, result.pe_sequence_number);
                }
            }
        } catch (error) {
            console.log('Failed to get sequence number');
        }

    },
    set_pe_journal_id_sequence(pe_journal_id, number_increment) {
        this.pe_sequences[pe_journal_id]=number_increment;
    },
    generate_sync_pe_move_name(pe_journal_id) {
        // Revisar
        var journal_id = this.session._pe_journal_by_id[pe_journal_id];
        var num = "%0"+journal_id.pe_padding+"d";
        var prefix = journal_id.pe_sequence_prefix || "";
        var increment = this.get_pe_journal_id_sequence(pe_journal_id)+1;
        var number = prefix + num.sprintf(parseInt(increment));
        return { 'pe_move_name': number, 'pe_sequence_number':increment};
    },
    get_pe_move_name(pe_journal_id){
        var number = this.generate_sync_pe_move_name(pe_journal_id);
        if (this.pe_move_names.indexOf(number.pe_move_name)!=-1){
            this.set_pe_journal_id_sequence(pe_journal_id, number.pe_sequence_number);
            this.pe_move_names.push(number.pe_move_name);
            number = this.get_pe_move_name(pe_journal_id);
        }
        this.set_pe_journal_id_sequence(pe_journal_id, number.pe_sequence_number);
        this.pe_move_names.push(number.pe_move_name);
        this.check_pe_sequence([pe_journal_id]);
        return number;
    },
    getReceiptHeaderData(order) {
        var res = super.getReceiptHeaderData(...arguments);
        if (order != undefined) {
            res['pe_invoice_name'] = order.pe_invoice_name;
            res['pe_move_name'] = order.pe_move_name;
            res['pe_src_move_name'] = order.pe_src_move_name;
            res['pe_annonymous_id'] = order.get_pe_annonymous_id();
        }
        return res;
    },
    get_pe_journal_id_sequence(pe_journal_id){
        var pe_sequences= this.pe_sequences;
        if (this.pe_sequences[pe_journal_id]){
            if (this.session._pe_journal_by_id[pe_journal_id].pe_sequence_number>pe_sequences[pe_journal_id]) {
                return  this.session._pe_journal_by_id[pe_journal_id].pe_sequence_number;
            }
            else {
                return pe_sequences[pe_journal_id];
            }
        }
        else{
            return this.session._pe_journal_by_id[pe_journal_id].pe_sequence_number;
        }
    },
    createNewOrder() {
        const order = super.createNewOrder(...arguments);
        if (this.isPeruvianCompany() && order.partner_id) {
            if (order.config_id.pe_auto_journal_select){
                order.calculate_pe_document_type();
            }
        }
        return order;
    },
});
