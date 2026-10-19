/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class ChipSelectorWidget extends Component {
    static template = "crm_custom_lead.ChipSelectorTemplate";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        // Inicialización si es necesaria
    }

    get options() {
        return [
            {
                value: 'sim_fisico',
                label: 'SIM Físico',
                image: '/crm_custom_lead/static/src/img/sim_fisico.png'
            },
            {
                value: 'sim_virtual',
                label: 'SIM Virtual',
                image: '/crm_custom_lead/static/src/img/sim_virtual.png'
            }
        ];
    }

    get selectedValue() {
        return this.props.record.data[this.props.name] || '';
    }

    isSelected(value) {
        return this.selectedValue === value;
    }

    async selectOption(value) {
        if (!this.props.readonly) {
            await this.props.record.update({ [this.props.name]: value });
        }
    }
}

registry.category("fields").add("chip_selector", {
    component: ChipSelectorWidget,
});