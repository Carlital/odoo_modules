odoo.define('l10n_pe_pos_cpe.PosResTicketScreen', function (require) {
    'use strict';

    const TicketScreen = require('point_of_sale.TicketScreen');
    const Registries = require('point_of_sale.Registries');

    const PosResTicketScreen = (TicketScreen) =>
        class extends TicketScreen {
            async _onDoRefund() {
                await super._onDoRefund();
                const order = this.getSelectedSyncedOrder();
                const new_order = this.env.pos.get_order();
                if(order.get_pe_journal_id()){
                    var journal_id = this.env.pos.db.get_pe_journals_by_id(order.get_pe_journal_id());
                    if (journal_id.pe_credit_note_id){
                        if (this.env.pos.db.get_pe_journals_by_id(journal_id.pe_credit_note_id[0])){
                            new_order.set_pe_journal_id(journal_id.pe_credit_note_id[0]);
                            new_order.pe_credit_note_code = '07'
                            new_order.pe_src_move_name = order.pe_move_name;
                        }
                    }
                }
                console.log(this);
            }
        };

    Registries.Component.extend(TicketScreen, PosResTicketScreen);

    return PosResTicketScreen;
});
