import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { unaccent } from "@web/core/utils/strings";

patch(ProductScreen.prototype, {
    getProductsBySearchWord(searchWord) {
        const words = searchWord.toLowerCase();
        const products = this.pos.selectedCategory?.id
            ? this.getProductsByCategory(this.pos.selectedCategory)
            : this.products;
        const exactMatches = products.filter((product) => product.exactMatch(words));

        if (exactMatches.length > 0 && words.length > 2) {
            return exactMatches;
        }

        const matches = products.filter((p) =>
            unaccent(p.searchString, false).toLowerCase().includes(words)
        );

        return Array.from(new Set([...exactMatches, ...matches]));
    }
});
