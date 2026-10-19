/** @odoo-module **/
import { WebsiteSale } from "@website_sale/js/website_sale";
// al renderizar la pagina de ecommerce ocultamos el precio de los productos
WebsiteSale.include({
    _render: function () {
        this._super.apply(this, arguments);
        $(".oe_currency_value").hide();
    }
});

