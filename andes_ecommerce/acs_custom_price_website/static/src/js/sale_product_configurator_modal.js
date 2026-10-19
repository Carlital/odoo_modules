/** @odoo-module */
import '@website_sale_product_configurator/js/sale_product_configurator_modal';
import Dialog from '@web/legacy/js/core/dialog';
import VariantMixin from '@website_sale/js/sale_variant_mixin';
import { uniqueId } from '@web/core/utils/functions';
import { jsonrpc } from '@web/core/network/rpc_service';

export const SaleProductConfiguratorModal = Dialog.extend({
    // inherit
    _onConfirmButtonClick: function () {
        console.log('confirm');
        this.trigger('confirm');
        this.close();
    },

});
