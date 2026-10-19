/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { deserializeDate, formatDate, formatDateTime, serializeDate } from "@web/core/l10n/dates";
const { DateTime } = luxon;

patch(PosStore.prototype, {
    //@override
    getReceiptHeaderData(order) {
        var res = super.getReceiptHeaderData(...arguments);
        if (order != undefined){
            var partner = order.get_partner();
            res['partner'] = partner;
            res['invoice_date'] = order.pe_invoice_date || DateTime.now().toFormat('yyyy-MM-dd HH:mm:ss'); // order.invoice_date;
            res['currency'] = order.currency;
        }
        return res;
    }
});
