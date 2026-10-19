/** @odoo-module */

import { PartnerList } from "@point_of_sale/app/screens/partner_list/partner_list";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { SelectDirectionPopup } from "@acs_multiaddress_pos_18/popups/select_direction_popup";

patch(PartnerList.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
    },

    async clickPartner(partner) {
        console.log('[ACS Multi Address] clickPartner called', partner);

        // Si partner es null/undefined (remover cliente), usar comportamiento original
        if (!partner) {
            console.log('[ACS Multi Address] No partner provided - removing customer');
            this.props.getPayload(null);
            this.props.close();
            return;
        }

        console.log('[ACS Multi Address] partner.clientes_varios:', partner.clientes_varios);
        console.log('[ACS Multi Address] partner.child_ids:', partner.child_ids);
        console.log('[ACS Multi Address] partner.vat:', partner.vat);
        console.log('[ACS Multi Address] partner.address_array:', partner.address_array);

        // Verificar todos los campos disponibles
        console.log('[ACS Multi Address] Todos los campos del partner:', Object.keys(partner));

        // Cliente "varios" - selección directa
        if (partner.clientes_varios) {
            console.log('[ACS Multi Address] Cliente varios - selección directa');
            this.props.getPayload(partner);
            this.props.close();
            return;
        }

        // Cliente con child_ids (direcciones adicionales)
        if (partner.child_ids && partner.child_ids.length > 0) {
            console.log('[ACS Multi Address] Mostrando popup - múltiples direcciones');
            await this._showAddressSelection(partner);
            return;
        }

        // Cliente con RUC (11 dígitos) sin child_ids
        // Usar vat ya que pe_doc_number es computado y no se almacena
        const docNumber = partner.vat || '';
        const cleanDocNumber = docNumber.replace(/^PE[RD]?/, ''); // Remover prefijo PE, PER o PED

        if (cleanDocNumber.length === 11) {
            console.log('[ACS Multi Address] Mostrando popup - RUC sin child_ids');
            await this._showSingleAddressSelection(partner);
            return;
        }

        // Cliente normal - selección directa
        console.log('[ACS Multi Address] Cliente normal - selección directa');
        this.props.getPayload(partner);
        this.props.close();
    },

    async _showAddressSelection(partner) {
        const result = await makeAwaitable(this.dialog, SelectDirectionPopup, {
            partner,
            singleMode: false,
        });

        if (!result) {
            return;
        }

        const selectedPartner = this._buildSelectedPartner(partner, result.selectedAddressId);

        if (result.other !== undefined && result.other !== partner.other) {
            await this._updatePartnerOther(partner.id, result.other);
            partner.other = result.other;
            selectedPartner.other = result.other;
        }

        this.props.getPayload(selectedPartner);
        this.props.close();
    },

    async _showSingleAddressSelection(partner) {
        const result = await makeAwaitable(this.dialog, SelectDirectionPopup, {
            partner,
            singleMode: true,
        });

        if (!result) {
            return;
        }

        const selectedPartner = this._buildSelectedPartner(partner, result.selectedAddressId);

        if (result.other !== undefined && result.other !== partner.other) {
            await this._updatePartnerOther(partner.id, result.other);
            partner.other = result.other;
            selectedPartner.other = result.other;
        }

        this.props.getPayload(selectedPartner);
        this.props.close();
    },

    _buildSelectedPartner(partner, addressId) {
        const partnerClone = this._clonePartner(partner);
        if (!addressId) {
            return partnerClone;
        }
        const selectedAddress = partner.address_array?.find((addr) => addr.id === addressId);
        if (!selectedAddress) {
            return partnerClone;
        }
        const fieldsToCopy = ['id', 'street', 'street2', 'address', 'city', 'state_id', 'country_id'];
        fieldsToCopy.forEach((field) => {
            if (field === 'id') {
                partnerClone.id_original = partner.id;
                partnerClone.id = selectedAddress.id;
            } else {
                partnerClone[field] = selectedAddress[field] ?? null;
            }
        });
        partnerClone.address = selectedAddress.address || this._formatAddress(selectedAddress);
        partnerClone.parent_id = partner.parent_id || [partner.id, partner.name];
        return partnerClone;
    },

    _clonePartner(partner) {
        const clone = Object.assign(Object.create(Object.getPrototypeOf(partner)), partner);
        clone.address_array = partner.address_array
            ? partner.address_array.map((addr) => ({ ...addr }))
            : [];
        clone.child_ids = partner.child_ids ? partner.child_ids.map((child) => child) : [];
        return clone;
    },

    _formatAddress(address) {
        const parts = [];
        if (address.street) parts.push(address.street);
        if (address.zip) parts.push(address.zip);
        if (address.city) parts.push(address.city);
        if (address.country_id && address.country_id[1]) parts.push(address.country_id[1]);
        return parts.join(', ');
    },

    async _updatePartnerOther(partnerId, otherValue) {
        await this.orm.call('res.partner', 'write', [partnerId, { other: otherValue }]);
    }
});
