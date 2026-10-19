/** @odoo-module */

import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { useState, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";

export class AddDirectionPopup extends Component {
    static template = "acs_multiaddress_pos_18.AddDirectionPopup";
    static components = { Dialog };
    static props = {
        partner: { type: Object, optional: true },
        getPayload: Function,  // Proporcionado por makeAwaitable
        close: { type: Function, optional: true },  // Proporcionado por makeAwaitable
    };

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            street: "",
            street2: "",
            city: "",
            country_id: null,
            countries: [],
        });

        onMounted(async () => {
            await this._loadCountries();
        });
    }

    get title() {
        return _t("Agregue datos");
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
        this.state.countries = countries;
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
        this.props.getPayload(this.getPayload());
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
