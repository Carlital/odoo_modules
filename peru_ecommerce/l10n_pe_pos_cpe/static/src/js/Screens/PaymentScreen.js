odoo.define('l10n_pe_pos_cpe.PosResPaymentScreen', function (require) {
    'use strict';

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');

    const PosResPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            async validateOrder(isForceValidate) {
                var order = this.currentOrder;
                if (!order.get_pe_journal_id() && this.env.pos.config.pe_force_journal_select){
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Journal not selected'),
                        body: this.env._t("Assign a journal according to the client's document type"),
                    });
                    return;
                }
                if (order.get_pe_journal_id() && !order.get_client() && this.env.pos.config.default_partner_id){
                    var new_client = this.env.pos.db.get_partner_by_id(this.env.pos.config.default_partner_id[0]);
                    if (new_client){
                        this.currentOrder.set_client(new_client);    
                    }
                }

                if (!order.get_pe_journal_id() && order.get_pe_move_name()){
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('There is assigned number'),
                        body: this.env._t("This order has an assigned number and must be sent as electronic proof "),
                    });
                    return;
                }
                if (order.get_pe_journal_id() && order.get_total_with_tax()>this.env.pos.company.pe_max_amount && !order.get_pe_doc_type()){
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Customer document error '),
                        body: this.env._t("Assign another customer with identification number "),
                    });
                    return;
                }
                if (order.get_pe_journal_id() && order.get_pe_doc_type() != '6'){
                    var journal_id = this.env.pos.db.get_pe_journals_by_id(order.get_pe_journal_id())
                    if (journal_id.pe_invoice_code=='01'){
                        this.showPopup('ErrorPopup', {
                            title: this.env._t('The invoice document error '),
                            body: this.env._t("The document type is not correct"),
                        });
                        return;
                    }
                }
                /*if (order.get_pe_journal_id() && order.get_total_tax()<0.0){
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Tax error '),
                        body: this.env._t("The tax must be greater than 0.0"),
                    });
                    return;
                }*/

                if(order.get_pe_journal_id() && !order.get_pe_move_name()){
                    var number = this.env.pos.get_pe_move_name(order.get_pe_journal_id());
                    order.set_pe_move_name(number.pe_move_name);
                }
                if (order.get_pe_move_name()){
                    var blob = new Blob([JSON.stringify(order.export_as_JSON())], {type: "text/plain;charset=utf-8"});
                    saveAs(blob, order.get_pe_move_name()+".json");    
                }
                return await super.validateOrder(isForceValidate);
            }
            toggleSetPeJournal(pe_journal_id) {
                if(this.currentOrder.get_pe_journal_id()==pe_journal_id){
                    this.currentOrder.set_pe_journal_id(false);
                }
                else{
                    this.currentOrder.set_pe_journal_id(pe_journal_id);
                }
                this.render();
            }
        };

    Registries.Component.extend(PaymentScreen, PosResPaymentScreen);

    return PosResPaymentScreen;
});
