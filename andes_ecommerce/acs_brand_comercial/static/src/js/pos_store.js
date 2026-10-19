/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
    getReceiptHeaderData(order) {
        const result = super.getReceiptHeaderData(...arguments);
        
        result.brand_comercial_data = {
            logotipo: this.config.logotipo,
            phone: this.config.phone,
            email: this.config.email,
            address: this.config.address,
        };
         
        return result;
    },
});
