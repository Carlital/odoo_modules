/** @odoo-module */

import { Navbar } from "@point_of_sale/app/navbar/navbar";
import { OrderCountComponent } from "@acs_pos_count_global/app/Screens/OrderCountComponent";
import { patch } from "@web/core/utils/patch";

patch(Navbar, {
    components: { ...Navbar.components, OrderCountComponent },
});
