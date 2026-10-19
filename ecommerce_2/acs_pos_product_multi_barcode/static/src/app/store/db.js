/** @odoo-module */

import { PosDB } from "@point_of_sale/app/store/db";
import { patch } from "@web/core/utils/patch";

patch(PosDB.prototype, {
    _product_search_string(product) {
        let str = super._product_search_string(...arguments);
        if (product.all_barcode_names) {
            const barcodes = product.all_barcode_names.split('\n').join('|');
            str = `${str.slice(0, -1)}|${barcodes}\n`;
        }
        return str;
    },
});
