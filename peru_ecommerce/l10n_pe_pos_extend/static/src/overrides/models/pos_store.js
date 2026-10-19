/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
    //@override
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.l10n_latam_identification_types_by_id = {};
        for (var i = 0, len = loadedData['l10n_latam.identification.type'].length; i < len; i++) {
            var l10n_latam_identification_type = loadedData['l10n_latam.identification.type'][i];
            this.l10n_latam_identification_types_by_id[l10n_latam_identification_type.id] = l10n_latam_identification_type;
        }
    },
    getReceiptHeaderData(order) {
        var res = super.getReceiptHeaderData(...arguments);
        var partner = order.get_partner();
        res['partner'] = partner;
        res['invoice_date'] = order.invoice_date;
        res['currency'] = order.pos.currency;
        return res;
    }
});
