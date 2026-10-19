/** @odoo-module */

import { Navbar } from "@point_of_sale/app/navbar/navbar";
import { PartnerSearchComponent } from "@acs_pos_partner_search/app/Screens/PartnerSearchComponent";
import { patch } from "@web/core/utils/patch";

patch(Navbar, {
    components: { ...Navbar.components, PartnerSearchComponent },
});
