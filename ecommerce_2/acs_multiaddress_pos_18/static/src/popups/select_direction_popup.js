/** @odoo-module */

import { Component, onWillStart } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { EditDirectionPopup } from "@acs_multiaddress_pos_18/popups/edit_direction_popup";
import { AddDirectionPopup } from "@acs_multiaddress_pos_18/popups/add_direction_popup";

export class SelectDirectionPopup extends Component {
    static template = "acs_multiaddress_pos_18.SelectDirectionPopup";
    static components = { Dialog };
    static props = {
        partner: Object,
        singleMode: { type: Boolean, optional: true },
        getPayload: Function,
        close: { type: Function, optional: true },
    };

    setup() {
        console.log("[SelectDirectionPopup] setup - Partner received:", this.props.partner);
        console.log("[SelectDirectionPopup] setup - singleMode:", this.props.singleMode);
        this.dialog = useService("dialog");
        this.orm = useService("orm");


        this.state = useState({
            selectedAddressId: null,
            other: this.props.partner?.other || "",
            addresses: this.props.partner?.address_array || [],
        });


        this.selectRef = useRef("addressSelect");
        this.otherRef = useRef("otherInput");

        onWillStart(async () => {
            console.log("[SelectDirectionPopup] onWillStart - About to ensure address array");
            await this._ensureAddressArray();
            console.log("[SelectDirectionPopup] onWillStart - Address array ensured, addresses:", this.state.addresses);
        });
    }

    get title() {
        return _t("Seleccione una dirección");
    }

    get confirmText() {
        return _t("Ok");
    }

    get cancelText() {
        return _t("Cancel");
    }

    getPayload() {
        const payload = {
            selectedAddressId: this.state.selectedAddressId,
            other: this.state.other,
        };
        console.log("[SelectDirectionPopup] getPayload - Returning payload:", payload);
        return payload;
    }

    confirm() {
        console.log("[SelectDirectionPopup] confirm - Called");
        const payload = this.getPayload();
        console.log("[SelectDirectionPopup] confirm - Sending payload:", payload);
        this.props.getPayload(payload);
        if (this.props.close) {
            this.props.close();
        }
    }

    cancel() {
        console.log("[SelectDirectionPopup] cancel - Called");
        this.props.getPayload(null);
        if (this.props.close) {
            this.props.close();
        }
    }

    onAddressChange(ev) {
        this.state.selectedAddressId = ev.target.value ? parseInt(ev.target.value) : null;
    }

    onOtherChange(ev) {
        this.state.other = ev.target.value;
    }

    async onEditAddress() {
        const selectedOption = this.selectRef.el?.selectedOptions[0];
        if (!selectedOption) return;

        const addressId = parseInt(selectedOption.dataset.edit);
        const originalId = parseInt(selectedOption.dataset.originalId);

        let addressToEdit;
        if (addressId === this.props.partner.id) {
            addressToEdit = this.props.partner;
        } else {
            addressToEdit = this.state.addresses?.find(addr => addr.id === addressId);
        }

        if (!addressToEdit) return;

        const result = await makeAwaitable(this.dialog, EditDirectionPopup, {
            address: addressToEdit,
        });

        if (result) {
            await this.orm.call('res.partner', 'write', [
                originalId || addressId,
                {
                    street: result.street,
                    street2: result.street2,
                    city: result.city,
                    country_id: result.country_id,
                }
            ]);

            addressToEdit.street = result.street;
            addressToEdit.street2 = result.street2;
            addressToEdit.city = result.city;
            addressToEdit.country_id = [result.country_id, result.country_name];
            addressToEdit.address = this._formatAddress(addressToEdit);

            // Actualizar el estado reactivo para forzar re-render
            this.state.addresses = [...this.state.addresses];
        }
    }

    async onAddAddress() {

        const result = await makeAwaitable(this.dialog, AddDirectionPopup, {
            partner: this.props.partner,
        });


        if (!result) {
            return;
        }

        // Crear nueva dirección como child del partner actual
        const newAddressData = {
            type: 'delivery',
            parent_id: this.props.partner.id,
            street: result.street,
            street2: result.street2,
            city: result.city,
            country_id: result.country_id,
            customer_rank: 0
        };


        try {
            // Crear la dirección en el backend
            const newAddressId = await this.orm.call('res.partner', 'create', [newAddressData]);

            // Crear objeto de dirección para el frontend
            const newAddress = {
                id: newAddressId,
                street: result.street,
                street2: result.street2,
                city: result.city,
                country_id: result.country_id ? [result.country_id, result.country_name] : false,
                type: 'delivery',
                parent_id: [this.props.partner.id, this.props.partner.name],
                address: this._formatAddress({
                    street: result.street,
                    city: result.city,
                    country_id: result.country_id ? [result.country_id, result.country_name] : false
                })
            };


            // Agregar a address_array del partner
            if (!this.props.partner.address_array) {
                this.props.partner.address_array = [];
            }
            this.props.partner.address_array.push(newAddress);

            // Agregar a child_ids
            if (!this.props.partner.child_ids) {
                this.props.partner.child_ids = [];
            }
            this.props.partner.child_ids.push(newAddressId);

            // Actualizar el estado reactivo para re-renderizar el select
            this.state.addresses = [...this.props.partner.address_array];

            // Seleccionar automáticamente la nueva dirección
            this.state.selectedAddressId = newAddressId;

            // Forzar actualización del DOM del select manualmente
            await this._updateSelectDOM(newAddress);

        } catch (error) {
        }
    }

    _formatAddress(address) {
        const parts = [];
        if (address.street) parts.push(address.street);
        if (address.zip) parts.push(address.zip);
        if (address.city) parts.push(address.city);
        if (address.country_id && address.country_id[1]) parts.push(address.country_id[1]);
        return parts.join(', ');
    }

    async _updateSelectDOM(newAddress) {

        // Usar nextTick para esperar a que Owl procese los cambios de estado
        await new Promise(resolve => setTimeout(resolve, 0));

        const selectElement = this.selectRef.el;

        if (!selectElement) {
            return;
        }

        // Crear el nuevo option element
        const newOption = document.createElement('option');
        newOption.value = newAddress.id;
        newOption.textContent = newAddress.address;
        newOption.setAttribute('data-edit', newAddress.id);
        newOption.setAttribute('data-original-id', newAddress.id);
        newOption.selected = true; // Seleccionarlo automáticamente


        // Agregar la opción al select
        selectElement.appendChild(newOption);

    }

    async _ensureAddressArray() {
        const partner = this.props.partner;
        if (!partner) {
            return;
        }


        const hasAddresses = partner.address_array && partner.address_array.length > 0;

        const childIdsRaw = partner.child_ids || [];
        const childIds = childIdsRaw
            .map((child) => {
                if (Array.isArray(child)) {
                    return child[0];
                }
                if (typeof child === "number") {
                    return child;
                }
                if (child && typeof child === "object") {
                    return child.id || child.res_id || child.child_id || null;
                }
                return null;
            })
            .filter((id) => typeof id === "number" && id > 0);


        if (hasAddresses || !childIds.length) {
            return;
        }
        const fields = [
            "id",
            "street",
            "street2",
            "zip",
            "city",
            "state_id",
            "country_id",
            "type",
            "parent_id",
        ];
        const children = await this.orm.read("res.partner", childIds, fields);

        const validChildren = (children || []).filter((child) =>
            ["delivery", "invoice"].includes(child.type || "") && child.parent_id
        );

        partner.address_array = validChildren.map((child) => {
            return {
                ...child,
                address: this._formatAddress(child),
            };
        });

        // Actualizar el estado reactivo
        this.state.addresses = [...partner.address_array];
    }
}
