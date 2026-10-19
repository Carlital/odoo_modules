/** @odoo-module */

import { ReceiptHeader } from "@point_of_sale/app/screens/receipt_screen/receipt/receipt_header/receipt_header";
import { patch } from "@web/core/utils/patch";

// We patch the component's static props to accept the new 'date' prop.
patch(ReceiptHeader, {
    props: {
        ...ReceiptHeader.props,
        date: { type: String, optional: true },
        name: { type: String, optional: true },
    },
});