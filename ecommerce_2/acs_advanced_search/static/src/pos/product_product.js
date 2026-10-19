import { ProductProduct } from "@point_of_sale/app/models/product_product";
import { patch } from "@web/core/utils/patch";

patch(ProductProduct.prototype, {
    exactMatch(searchQuery) {
        const fields = ["barcode", "default_code", "standard_name", "name"];
        const words = searchQuery.toLowerCase().split(/\s+/).filter(Boolean);
    
        return words.every(word =>
            fields.some(field => this[field] && this[field].toLowerCase().includes(word))
        );
    }
});
