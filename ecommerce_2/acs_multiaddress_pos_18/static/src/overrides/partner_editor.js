/** @odoo-module */

import { PartnerDetailsEdit } from "@point_of_sale/app/screens/partner_list/partner_editor/partner_editor";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(PartnerDetailsEdit.prototype, {
    setup() {
        super.setup(...arguments);
        this.popup = useService("popup");
    },

    async onAddExtraAddress() {
        const { confirmed, payload } = await this.popup.add("AddDirectionPopup", {
            partner: this.props.partner,
        });

        if (confirmed) {
            if (!this.props.partner.extra_addresses) {
                this.props.partner.extra_addresses = [];
            }

            this.props.partner.extra_addresses.push({
                street: payload.street,
                street2: payload.street2,
                city: payload.city,
                country_id: payload.country_id,
                country_name: payload.country_name,
            });

            this.render();
        }
    },

    onDeleteAddress(index) {
        if (this.props.partner.extra_addresses) {
            this.props.partner.extra_addresses.splice(index, 1);
            this.render();
        }
    }
});
