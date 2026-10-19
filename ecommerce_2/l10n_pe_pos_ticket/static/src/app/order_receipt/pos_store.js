/** @odoo-module */

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    /**
     * Sobrescribe el método para añadir los campos peruanos a la carga
     */
    getLoadDataModels() {
        const models = super.getLoadDataModels();
        
        // Encontrar el modelo res.partner y agregar los campos
        const partnerModel = models.find(model => model.model === 'res.partner');
        if (partnerModel && partnerModel.fields) {
            const fieldsToAdd = ['l10n_pe_district', 'city_id', 'state_id'];
            fieldsToAdd.forEach(field => {
                if (!partnerModel.fields.includes(field)) {
                    partnerModel.fields.push(field);
                }
            });
        }
        
        return models;
    },

    /**
     * Procesa los datos después de cargarlos para convertir Many2one
     */
    async load_server_data() {
        const result = await super.load_server_data();
        
        // Convertir campos Many2one de partners a formato [id, nombre]
        if (this.models['res.partner']) {
            for (const partnerId in this.models['res.partner']) {
                const partner = this.models['res.partner'][partnerId];
                
                // Convertir city_id
                if (partner.city_id && typeof partner.city_id === 'number') {
                    const city = this.models['res.city']?.[partner.city_id];
                    partner.city_id = city ? [city.id, city.name] : false;
                }
                
                // Convertir state_id
                if (partner.state_id && typeof partner.state_id === 'number') {
                    const state = this.models['res.country.state']?.[partner.state_id];
                    partner.state_id = state ? [state.id, state.name] : false;
                }
                
                // Convertir country_id (por si acaso)
                if (partner.country_id && typeof partner.country_id === 'number') {
                    const country = this.models['res.country']?.[partner.country_id];
                    partner.country_id = country ? [country.id, country.name] : false;
                }
                
                // Convertir l10n_pe_district
                if (partner.l10n_pe_district) {
                    if (typeof partner.l10n_pe_district === 'number') {
                        const district = this.models['l10n_pe.res.city.district']?.[partner.l10n_pe_district];
                        partner.l10n_pe_district = district ? [district.id, district.name] : false;
                    } else if (typeof partner.l10n_pe_district === 'string') {
                        // Si es string (campo Char), convertir a formato [false, string]
                        partner.l10n_pe_district = [false, partner.l10n_pe_district];
                    }
                }
            }
        }
        
        return result;
    }
});