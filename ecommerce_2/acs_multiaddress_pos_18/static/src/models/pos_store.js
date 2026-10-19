/** @odoo-module */

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { ResPartner } from "@point_of_sale/app/models/res_partner";

// Extender el modelo res.partner para agregar procesamiento de direcciones
patch(ResPartner.prototype, {
    setup(vals) {
        super.setup(...arguments);
        this.address_array = [];
    },
});

patch(PosStore.prototype, {
    // Hook después de que se carguen todos los datos
    async after_load_server_data() {
        await super.after_load_server_data(...arguments);
        await this._processPartnerAddressesAll(this.models["res.partner"].getAll());
    },

    async _processPartnerAddressesAll(partnersTarget) {
        const fallback = this.models["res.partner"]?.getAll ? this.models["res.partner"].getAll() : [];
        const target = partnersTarget || fallback;
        const partnersById = {};
        const childPartners = [];
        const parentPartners = [];

        // Separar padres e hijos
        target.forEach(partner => {
            partnersById[partner.id] = partner;
            if (partner.parent_id) {
                partner.address = this._formatAddress(partner);
                childPartners.push(partner);
            } else {
                if (!partner.address_array) {
                    partner.address_array = [];
                }
                parentPartners.push(partner);
            }
        });

        // Asignar hijos a padres
        childPartners.forEach(child => {
            if (child.parent_id && child.parent_id.length > 0) {
                const parentId = Array.isArray(child.parent_id) ? child.parent_id[0] : child.parent_id;
                const parent = partnersById[parentId];
                if (parent && parent.address_array) {
                    parent.address_array.push(child);
                }
            }
        });
    },

    _processPartnerAddresses(partners) {
        const childPartners = [];
        const parentPartners = [];
        const partnersById = {};

        partners.forEach(partner => {
            partnersById[partner.id] = partner;
            if (partner.parent_id) {
                partner.address = this._formatAddress(partner);
                childPartners.push(partner);
            } else {
                partner.address_array = [];
                parentPartners.push(partner);
            }
        });

        childPartners.forEach(child => {
            const parentId = child.parent_id[0];
            const parent = partnersById[parentId];
            if (parent) {
                parent.address_array.push(child);
            }
        });

        return parentPartners;
    },

    _formatAddress(partner) {
        const parts = [];
        if (partner.street) parts.push(partner.street);
        if (partner.zip) parts.push(partner.zip);
        if (partner.city) parts.push(partner.city);
        if (partner.country_id && partner.country_id[1]) parts.push(partner.country_id[1]);
        return parts.join(', ');
    },

    async loadNewPartners() {
        if (this.models["res.partner"] && typeof this.models["res.partner"].getLastWriteDate === "function") {
            const lastWriteDate = this.models["res.partner"].getLastWriteDate();
            const domain = [
                "|", ["customer_rank", ">", 0], ["parent_id", "!=", false],
                ["write_date", ">", lastWriteDate]
            ];

            const newPartners = await this.data.searchRead(
                "res.partner",
                domain,
                [
                    "name", "street", "city", "state_id", "country_id", "vat",
                    "phone", "zip", "mobile", "email", "barcode", "write_date",
                    "property_account_position_id", "property_product_pricelist",
                    "parent_id", "child_ids", "other", "clientes_varios"
                ]
            );

            const childPartners = [];
            const parentPartners = [];

            newPartners.forEach(partner => {
                if (partner.parent_id) {
                    partner.address = this._formatAddress(partner);
                    childPartners.push(partner);
                } else {
                    partner.address_array = [];
                    parentPartners.push(partner);
                }
            });

            childPartners.forEach(child => {
                const parentId = child.parent_id[0];
                const existingParent = this.models["res.partner"].get(parentId);

                if (existingParent) {
                    if (!existingParent.address_array) {
                        existingParent.address_array = [];
                    }
                    existingParent.address_array.push(child);
                } else {
                    const newParent = parentPartners.find(p => p.id === parentId);
                    if (newParent) {
                        newParent.address_array.push(child);
                    }
                }
            });

            if (parentPartners.length > 0) {
                this.models["res.partner"].loadData(parentPartners);
            }

            return parentPartners.length > 0;
        }

        const newPartners = await this.data.searchRead(
            "res.partner",
            ["|", ["customer_rank", ">", 0], ["parent_id", "!=", false]],
            [
                "name", "street", "city", "state_id", "country_id", "vat",
                "phone", "zip", "mobile", "email", "barcode", "write_date",
                "property_account_position_id", "property_product_pricelist",
                "parent_id", "child_ids", "other", "clientes_varios"
            ]
        );

        await this._processPartnerAddressesAll();
        return true;
    }
});
