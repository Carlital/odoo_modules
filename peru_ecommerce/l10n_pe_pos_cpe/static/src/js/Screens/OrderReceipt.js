odoo.define('l10n_pe_pos_cpe.PosResOrderReceipt', function (require) {
    'use strict';

    const OrderReceipt = require('point_of_sale.OrderReceipt');
    const Registries = require('point_of_sale.Registries');

    const PosResOrderReceipt = (OrderReceipt) =>
        class extends OrderReceipt {
            constructor() {
                super(...arguments);
            }
            willUpdateProps(nextProps) {
                return super.willUpdateProps(nextProps);
            }
        };

    Registries.Component.extend(OrderReceipt, PosResOrderReceipt);

    return PosResOrderReceipt;
});
