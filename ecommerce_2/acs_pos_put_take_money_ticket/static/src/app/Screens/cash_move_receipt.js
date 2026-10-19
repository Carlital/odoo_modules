import { Component } from "@odoo/owl";

export class CashMoveReceiptACS extends Component {
    static template = "acs_pos_put_take_money_ticket.CashMoveReceipt";
    static props = {
        reason: String,
        translatedType: String,
        formattedAmount: String,
        headerData: Object,
        date: String,
    };
}
