/** @odoo-module **/

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";

patch(ProductScreen.prototype, {
    get productsToDisplay() {
        const products = super.productsToDisplay;

        if (!products || products.length === 0) {
            return products;
        }

        return [...products].sort((a, b) => {
            const priorityA = a.acs_sort_pos_product ?? 0;
            const priorityB = b.acs_sort_pos_product ?? 0;

            if (priorityA !== priorityB) {
                return priorityB - priorityA;
            }

            const nameA = (a.display_name || '').toLowerCase();
            const nameB = (b.display_name || '').toLowerCase();
            return nameA.localeCompare(nameB);
        });
    },
});
