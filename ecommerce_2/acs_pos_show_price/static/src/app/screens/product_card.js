import { ProductProduct } from "@point_of_sale/app/models/product_product";
import { patch } from "@web/core/utils/patch";

patch(ProductProduct.prototype, {
    get price_base() {
        const rules = this.cachedPricelistRules;
        // Obtener las keys del objeto como array
        const keys = Object.keys(rules);

        // Encontrar la primera key que tenga un array no vacío
        let firstRule = undefined;
        for (const key of keys) {
            const arr = rules[key];
            if (Array.isArray(arr) && arr.length > 0) {
                firstRule = arr[0];
                break;
            }
        }
        let lst_price = this.lst_price;
        if(firstRule){
            lst_price = this.get_price(firstRule,1,0,true,this.lst_price)
        }
        // Si no hay nada, firstRule será undefined
        console.log(firstRule);
        const formateado = `$${lst_price.toFixed(2)}`;
        return formateado

    },
    
});
