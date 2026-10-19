/** @odoo-module */
import "@website_sale_product_configurator/js/website_sale_options";
import publicWidget from "@web/legacy/js/public/public_widget";
import { CartManagerMixin } from "@theme_prime/js/core/mixins";
import { QuickViewDialog } from "@theme_prime/js/frontend/quick_view_dialog";
import wSaleUtils from "@website_sale/js/website_sale_utils";


publicWidget.registry.WebsiteSale.include(Object.assign({}, CartManagerMixin, {

    _onModalSubmit: function (goToShop) {
        const mainProduct = this.$('.js_product.in_cart.main_product').children('.product_id');
        const productTrackingInfo = mainProduct.data('product-tracking-info');
        var custom_price = 0;

        if (productTrackingInfo) {
            const currency = productTrackingInfo['currency'];
            const productsTrackingInfo = [];

            this.$('.js_product.in_cart').each((i, el) => {
                // si encuentra el input  custom_price en la vista toma ese valor sino toma valor cero

                if (el.getElementsByClassName('custom_price').length === 0) {
                    custom_price = 0;
                }
                else {
                    custom_price = parseInt(el.getElementsByClassName('custom_price')[0].value);
                }

                productsTrackingInfo.push({
                    'item_id': parseInt(el.getElementsByClassName('product_id')[0].value),
                    'item_name': el.getElementsByClassName('product_display_name')[0].textContent,
                    'quantity': parseFloat(el.getElementsByClassName('js_quantity')[0].value) || 1,
                    'currency': currency,
                    'price': custom_price,
                });
                // custom_price = parseInt(el.getElementsByClassName('custom_price')[0].value);

            });
            if (productsTrackingInfo.length) {
                this.$el.trigger('add_to_cart_event', productsTrackingInfo);
            }
        }

        const callService = this.call.bind(this)
        this.optionalProductsModal.getAndCreateSelectedProducts()
            .then((products) => {


                // a produtcs agregale el custom_price este viene de la vista el input con id custom_price
                products.forEach(product => {
                    product.custom_price = custom_price;
                });

                const productAndOptions = JSON.stringify(products);
                this.rpc('/shop/cart/update_option', {
                    product_and_options: productAndOptions,
                    ...this._getOptionalCombinationInfoParam(),
                }).then(function (values) {
                    if (goToShop) {
                        window.location.pathname = "/shop/cart";
                    } else {
                        wSaleUtils.updateCartNavBar(values);
                        wSaleUtils.showCartNotification(callService, values.notification_info);
                    }
                }).then(() => {
                    this._getCombinationInfo($.Event('click', { target: $("#add_to_cart") }));
                });
            });
    },
}));