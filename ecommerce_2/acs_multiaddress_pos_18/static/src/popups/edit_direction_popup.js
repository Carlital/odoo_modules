/** @odoo-module */

import { Component, onWillStart } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";

export class EditDirectionPopup extends Component {
    static template = "acs_multiaddress_pos_18.EditDirectionPopup";
    static components = { Dialog };
    static props = {
        address: { type: Object, optional: true },
        getPayload: Function,  // Proporcionado por makeAwaitable
        close: { type: Function, optional: true },  // Proporcionado por makeAwaitable
    };

    setup() {
        this.orm = useService("orm");
        const rawCountry = this.props.address?.country_id;
        let countryId = null;
        let countryName = "";
        if (Array.isArray(rawCountry)) {
            countryId = rawCountry[0];
            countryName = rawCountry[1] || "";
        } else if (typeof rawCountry === "number") {
            countryId = rawCountry;
        } else if (rawCountry && typeof rawCountry === "object") {
            countryId = rawCountry.id || rawCountry.res_id || null;
            countryName = rawCountry.name || rawCountry.display_name || "";
        }

        const initialCountries = [];
        if (countryId) {
            initialCountries.push({ id: countryId, name: countryName });
        }

        this.state = useState({
            street: this.props.address?.street || "",
            street2: this.props.address?.street2 || "",
            city: this.props.address?.city || "",
            country_id: countryId,
            countries: initialCountries,
        });

        onWillStart(async () => {
            await this._loadCountries();
            if (this.state.country_id && !this.state.countries.find((c) => c.id === this.state.country_id)) {
                const countryData = await this.orm.read("res.country", [this.state.country_id], ["id", "name"]);
                if (countryData && countryData.length) {
                    this.state.countries = [...this.state.countries, countryData[0]];
                }
            }
        });
    }

    get title() {
        return _t("Editar la Dirección");
    }

    get confirmText() {
        return _t("Guardar");
    }

    get cancelText() {
        return _t("Cancelar");
    }

    async _loadCountries() {
        const countries = await this.orm.searchRead(
            "res.country",
            [],
            ["id", "name"],
            { order: "name" }
        );
        const existingIds = new Set(this.state.countries.map((c) => c.id));
        const merged = [...this.state.countries];
        countries.forEach((country) => {
            if (!existingIds.has(country.id)) {
                merged.push(country);
            }
        });
        this.state.countries = merged;
    }

    getPayload() {
        const selectedCountry = this.state.countries.find(c => c.id === this.state.country_id);
        return {
            street: this.state.street,
            street2: this.state.street2,
            city: this.state.city,
            country_id: this.state.country_id,
            country_name: selectedCountry?.name || "",
        };
    }

    confirm() {
        const payload = this.getPayload();
        this.props.getPayload(payload);
        if (this.props.close) {
            this.props.close();
        }
    }

    cancel() {
        this.props.getPayload(null);
        if (this.props.close) {
            this.props.close();
        }
    }

    onInputChange(field, ev) {
        if (field === 'country_id') {
            this.state[field] = ev.target.value ? parseInt(ev.target.value) : null;
        } else {
            this.state[field] = ev.target.value;
        }
    }
}
