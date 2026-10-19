odoo.define('barcode_quantity_popup.popup_quantity', function (require) {
    "use strict";

    const models = require('point_of_sale.models');
    const Dialog = require('web.Dialog');
    const { _t } = require('web.core');

    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '/barcode_quantity_popup/static/src/css/popup_quantity.css';
    document.head.appendChild(link);

    const OrderlineSuper = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function (attributes, options) {
            OrderlineSuper.initialize.apply(this, arguments);

            if (options.product) {
                this._showQuantityPopup(options.product);
            }
        },

        _showQuantityPopup: function (product) {
            let quantity = 1;
            const popupDialog = new Dialog(null, {
                size: 'medium',
                $content: $(`
                    <div class="popup-quantity-container">
                        <h3 class="popup-title">${_t("Configura la cantidad del producto")}</h3>
                        <div class="popup-content">
                            <button class="popup-button" id="decrement">-</button>
                            <input type="number" id="product_quantity" value="${quantity}" min="1" class="popup-input">
                            <button class="popup-button" id="increment">+</button>
                        </div>
                        <div class="popup-buttons-container">
                            <button class="popup-button-confirm">${_t("Aceptar")}</button>
                        </div>
                    </div>
                `),
                buttons: [],
            });

            popupDialog.open();

            $(document).off('click', '#increment');
            $(document).off('click', '#decrement');
            $(document).off('click', '.popup-button-confirm');

            $(document).on('click', '#increment', function () {
                const current = parseInt($('#product_quantity').val(), 10) || 0;
                $('#product_quantity').val(current + 1);
            });

            $(document).on('click', '#decrement', function () {
                const current = parseInt($('#product_quantity').val(), 10) || 0;
                if (current > 1) {
                    $('#product_quantity').val(current - 1);
                }
            });

            $(document).on('click', '.popup-button-confirm', () => {
                const selectedQuantity = parseInt($('#product_quantity').val(), 10);
                console.log(`Cantidad seleccionada para ${product.display_name}: ${selectedQuantity}`);
                this.set_quantity(selectedQuantity);
                popupDialog.close();
            });
        },
    });
});
