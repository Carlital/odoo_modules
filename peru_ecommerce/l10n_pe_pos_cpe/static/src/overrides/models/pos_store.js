/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { formatDate } from "@web/core/l10n/dates";

patch(PosStore.prototype, {
    //@override
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.pe_journals = loadedData['account.journal'];
        this.db.add_pe_journals(this.pe_journals);
    },
    getReceiptHeaderData(order) {
        var res = super.getReceiptHeaderData(...arguments);
        var partner = order.get_partner();
        return res;
    },

    addPeJournals(pe_journals) {
        return this.db.add_pe_journals(pe_journals);
    },
    async check_pe_sequence(pe_journal_ids) {
        var self = this;
        try {
            var result = await this.orm.call(
                "account.journal",
                "get_pe_sequence",
                [pe_journal_ids]
            );
            for (var i = 0; i < pe_journal_ids.length; i++) {
                if(result[pe_journal_ids[i]].pe_sequence_number>self.db.get_pe_journal_id_sequence(pe_journal_ids[i])){
                    self.db.set_pe_journal_id_sequence(pe_journal_id, result.pe_sequence_number);
                }
            }
        } catch (error) {
            console.log('Failed to get sequence number');
        }

    },
    generate_sync_pe_move_name(pe_journal_id) {
        var journal_id = this.db.get_pe_journals_by_id(pe_journal_id);
        var num = "%0"+journal_id.pe_padding+"d";
        var prefix = journal_id.pe_sequence_prefix || "";
        var increment = this.db.get_pe_journal_id_sequence(pe_journal_id)+1;
        var number = prefix + num.sprintf(parseInt(increment));
        return { 'pe_move_name': number, 'pe_sequence_number':increment};
    },
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
    },
    getReceiptHeaderData(order) {
        var res = super.getReceiptHeaderData(...arguments);
        res['pe_invoice_name'] = order.pe_invoice_name;
        res['pe_move_name'] = order.pe_move_name;
        res['pe_src_move_name'] = order.pe_src_move_name;
        return res;
    }
});
