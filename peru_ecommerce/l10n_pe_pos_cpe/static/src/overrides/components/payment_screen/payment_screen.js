/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { _t } from "@web/core/l10n/translation";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.pe_journal_ids =  this.currentOrder.get_valid_pe_journal_ids();
    },
    async validateOrder(isForceValidate) {
        var order = this.currentOrder;
        if (!order.get_pe_journal_id() && this.pos.config.pe_force_journal_select){
            this.popup.add(ErrorPopup, {
                title: _t('Journal not selected'),
                body: _t("Assign a journal according to the client's document type"),
            });
            return;
        }
        /*if (order.get_pe_journal_id() && !order.get_partner() && this.pos.config.default_partner_id){
            var new_partner = this.pos.db.get_partner_by_id(this.pos.config.default_partner_id[0]);
            if (new_partner){
                this.currentOrder.set_partner(new_partner);
            }
        }*/
        if (order.get_pe_journal_id() && !order.get_partner()){
            this.popup.add(ErrorPopup, {
                title: _t('Customer not selected'),
                body: _t("Assign a customer according to the client's document type"),
            });
            return;
        }
        if (!order.get_pe_journal_id() && order.get_pe_move_name()){
            this.popup.add(ErrorPopup, {
                title: _t('There is assigned number'),
                body: _t("This order has an assigned number and must be sent as electronic proof "),
            });
            return;
        }
        if (order.get_pe_journal_id() && order.get_total_with_tax()>this.pos.company.pe_max_amount && !order.get_pe_doc_type()){
            this.popup.add(ErrorPopup, {
                title: _t('Customer document error '),
                body: _t("Assign another customer with identification number "),
            });
            return;
        }
        if (order.get_pe_journal_id() && order.get_pe_doc_type() != '6'){
            var journal_id = this.pos.db.get_pe_journals_by_id(order.get_pe_journal_id())
            if (journal_id.pe_invoice_code=='01'){
                this.popup.add(ErrorPopup, {
                    title: _t('The invoice document error '),
                    body: _t("The document type is not correct"),
                });
                return;
            }
        }
        /*if (order.get_pe_journal_id() && order.get_total_tax()<0.0){
            this.showPopup(ErrorPopup, {
                title: _t('Tax error '),
                body: _t("The tax must be greater than 0.0"),
            });
            return;
        }*/

        if(order.get_pe_journal_id() && !order.get_pe_move_name()){
            await this.pos.check_pe_sequence([order.get_pe_journal_id()]);
            var number = this.pos.get_pe_move_name(order.get_pe_journal_id());
            if (number){
                order.set_pe_move_name(number.pe_move_name);
            }
        }
        if (order.get_pe_move_name()){
            var blob = new Blob([JSON.stringify(order.export_as_JSON())], {type: "text/plain;charset=utf-8"});
            saveAs(blob, order.get_pe_move_name()+".json");
        }
        return await super.validateOrder(isForceValidate);
    },
    toggleSetPeJournal(self, pe_journal_id) {
        if(self.currentOrder.get_pe_journal_id()==pe_journal_id){
            self.currentOrder.set_pe_journal_id(false);
        }
        else{
            self.currentOrder.set_pe_journal_id(pe_journal_id);
        }
        self.pos.check_pe_sequence([pe_journal_id]);
        //self.render(true);
    }
});
