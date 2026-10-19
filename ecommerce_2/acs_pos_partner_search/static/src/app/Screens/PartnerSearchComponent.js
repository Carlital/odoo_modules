/** @odoo-module */

import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Input } from "@point_of_sale/app/generic_components/inputs/input/input";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { SelectDirectionPopup } from "@acs_multiaddress_pos_18/popups/select_direction_popup";

export class PartnerSearchComponent extends Component {
    static template = "acs_pos_partner_search.PartnerSearchComponent";
    static components = { Input };
    static props = ["close?"];
    setup() {
        this.ui = useState(useService("ui"));
        this.pos = usePos();
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.notification = useService("notification");
        this.state = useState({
            searchValue: "",
            results: [],
        });
    }

    async onInputChange(ev) {
        this.searchValue = ev.target.value;
        this.state.searchValue = ev.target.value;
        if (!this.state.searchValue) {
            this.state.results = [];
            return;
        }
        try {
            const result = await this.orm.call("res.partner", "get_partners", [this.state.searchValue]);
            const resultArray = result ? Object.values(result) : [];
            this.state.results = resultArray;
        } catch (error) {
            console.error("Error al obtener partners:", error);
            this.state.results = [];
        }
    }

    async onSelectPartner(partner) {
        const posPartner = await this._getPosPartnerById(partner.id);
        if (!posPartner) {
            return;
        }
        await this._assignPartnerWithPopup(posPartner);
    }

    async onSavePartner() {
        console.log("[ACS POS Partner Search] onSavePartner - searchValue:", this.state.searchValue);
        const newPartner = await this.orm.call("res.partner", "get_by_doc_number", [this.state.searchValue]);
        console.log("[ACS POS Partner Search] onSavePartner - Response from get_by_doc_number:", newPartner);

        if (newPartner.state === 302) {
            console.log("[ACS POS Partner Search] onSavePartner - Error 302:", newPartner.msg);
            this.notification.add(newPartner.msg, {
                type: "warning",
                title: "Busqueda SUNAT",
            });
            return;
        }

        if (newPartner.state === 200) {
            console.log("[ACS POS Partner Search] onSavePartner - Success 200:", newPartner.msg);
            this.notification.add(newPartner.msg, {
                type: "success",
                title: "Busqueda SUNAT",
            });
        }

        console.log("[ACS POS Partner Search] onSavePartner - Loading new partners...");
        await this.pos.loadNewPartners();
        const posPartner = await this._getPosPartnerById(newPartner.partner_id, false);
        console.log("[ACS POS Partner Search] onSavePartner - POS Partner loaded:", posPartner);
        if (posPartner) {
            await this._assignPartnerWithPopup(posPartner);
        }
    }

    async _assignPartnerWithPopup(partner) {
        const selectedPartner = await this._maybeHandleAddressSelection(partner);
        if (!selectedPartner) {
            return false;
        }

        const order = this.pos.get_order();
        order.set_partner(selectedPartner);
        this._clearSearch();
        return true;
    }

    async _maybeHandleAddressSelection(partner) {
        console.log("[ACS POS Partner Search] _maybeHandleAddressSelection - Partner:", partner);
        if (!partner) {
            console.log("[ACS POS Partner Search] _maybeHandleAddressSelection - No partner, returning false");
            return false;
        }
        partner.address_array = partner.address_array || [];

        if (partner.clientes_varios) {
            console.log("[ACS POS Partner Search] _maybeHandleAddressSelection - Cliente varios, returning partner");
            return partner;
        }

        const hasChildren = partner.child_ids && partner.child_ids.length > 0;
        const docNumber = this._cleanDocNumber(partner.vat);
        console.log("[ACS POS Partner Search] _maybeHandleAddressSelection - VAT:", partner.vat, "Cleaned:", docNumber);
        const isDNI = docNumber.length === 8;
        const isRUC = docNumber.length === 11;
        const requiresPopup = hasChildren || isDNI || isRUC;
        console.log("[ACS POS Partner Search] _maybeHandleAddressSelection - hasChildren:", hasChildren, "isDNI:", isDNI, "isRUC:", isRUC, "requiresPopup:", requiresPopup);

        if (!requiresPopup) {
            console.log("[ACS POS Partner Search] _maybeHandleAddressSelection - No popup required, returning partner");
            return partner;
        }

        console.log("[ACS POS Partner Search] _maybeHandleAddressSelection - Opening SelectDirectionPopup with singleMode:", !hasChildren && (isDNI || isRUC));
        const result = await makeAwaitable(this.dialog, SelectDirectionPopup, {
            partner,
            singleMode: !hasChildren && (isDNI || isRUC),
        });

        console.log("[ACS POS Partner Search] _maybeHandleAddressSelection - Popup result:", result);
        if (!result) {
            console.log("[ACS POS Partner Search] _maybeHandleAddressSelection - No result from popup, returning null");
            return null;
        }

        if (result.other !== undefined && result.other !== partner.other) {
            await this._updatePartnerOther(partner.id, result.other);
            partner.other = result.other;
        }

        if (result.selectedAddressId) {
            const selectedAddress = partner.address_array?.find((addr) => addr.id === result.selectedAddressId);

            if (selectedAddress) {
                partner.street = selectedAddress.street || "";
                partner.street2 = selectedAddress.street2 || "";
                partner.city = selectedAddress.city || "";
                partner.address = selectedAddress.address || this._formatAddress(selectedAddress);

                if (selectedAddress.country_id) {
                    partner.country_id = Array.isArray(selectedAddress.country_id)
                        ? selectedAddress.country_id
                        : [selectedAddress.country_id, ""];
                }

                if (selectedAddress.state_id) {
                    partner.state_id = Array.isArray(selectedAddress.state_id)
                        ? selectedAddress.state_id
                        : [selectedAddress.state_id, ""];
                }
            }
        }

        return partner;
    }

    _buildSelectedPartner(partner, addressId) {
        if (!addressId) {
            return partner;
        }

        const selectedAddress = partner.address_array?.find((addr) => addr.id === addressId);
        if (!selectedAddress) {
            return partner;
        }

        if (!partner.id_original) {
            partner.id_original = partner.id;
        }

        partner.id = selectedAddress.id;
        partner.street = selectedAddress.street || "";
        partner.street2 = selectedAddress.street2 || "";
        partner.city = selectedAddress.city || "";
        partner.address = selectedAddress.address || this._formatAddress(selectedAddress);

        if (selectedAddress.state_id) {
            partner.state_id = Array.isArray(selectedAddress.state_id)
                ? selectedAddress.state_id
                : [selectedAddress.state_id, ""];
        } else {
            partner.state_id = false;
        }

        if (selectedAddress.country_id) {
            partner.country_id = Array.isArray(selectedAddress.country_id)
                ? selectedAddress.country_id
                : [selectedAddress.country_id, ""];
        } else {
            partner.country_id = false;
        }

        if (!partner.parent_id) {
            partner.parent_id = [partner.id_original, partner.name];
        }

        const relationalFields = [
            'category_id', 'property_product_pricelist', 'property_account_position_id',
            'user_id', 'commercial_partner_id', 'company_id', 'title'
        ];

        relationalFields.forEach(field => {
            if (partner[field] === undefined) {
                partner[field] = false;
            }
        });

        return partner;
    }

    _clonePartner(partner) {
        const clone = Object.assign(Object.create(Object.getPrototypeOf(partner)), partner);
        clone.address_array = partner.address_array ? partner.address_array.map((addr) => ({ ...addr })) : [];
        clone.child_ids = partner.child_ids ? partner.child_ids.map((child) => child) : [];
        return clone;
    }

    _formatAddress(address) {
        const parts = [];
        if (address.street) parts.push(address.street);
        if (address.zip) parts.push(address.zip);
        if (address.city) parts.push(address.city);
        if (address.country_id && address.country_id[1]) parts.push(address.country_id[1]);
        return parts.join(", ");
    }

    async _updatePartnerOther(partnerId, otherValue) {
        await this.orm.call("res.partner", "write", [[partnerId], { other: otherValue }]);
    }

    async _getPosPartnerById(partnerId, allowReload = true) {
        let posPartner = this.pos.models["res.partner"].getBy("id", partnerId);
        if (!posPartner && allowReload) {
            await this.pos.loadNewPartners();
            posPartner = this.pos.models["res.partner"].getBy("id", partnerId);
        }
        return posPartner;
    }

    _cleanDocNumber(vat) {
        if (!vat || vat === false) {
            return "";
        }
        return String(vat).replace(/^PE[RD]?/, "").trim();
    }

    _clearSearch() {
        this.state.results = [];
        this.state.searchValue = "";
        this.searchValue = "";
    }
}
