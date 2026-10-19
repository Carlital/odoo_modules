/** @odoo-module */

import { Navbar } from "@point_of_sale/app/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { Component } from "@odoo/owl";

patch(Navbar.prototype, {
    setup() {
        super.setup(...arguments);
    }
});
