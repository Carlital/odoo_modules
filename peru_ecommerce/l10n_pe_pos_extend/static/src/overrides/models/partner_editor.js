/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { patch } from "@web/core/utils/patch";
import { PartnerDetailsEdit } from "@point_of_sale/app/screens/partner_list/partner_editor/partner_editor";
import { useService } from "@web/core/utils/hooks";

patch(PartnerDetailsEdit.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
    },
    async updatePeValues(event){
        var l10n_latam_identification_type_id = this.changes['l10n_latam_identification_type_id'];
        var vat = this.changes['vat']
        var self = this;
        if (l10n_latam_identification_type_id) {
            var pe_doc_type = this.pos.l10n_latam_identification_types_by_id[parseInt(l10n_latam_identification_type_id)].l10n_pe_vat_code;
        }
        else {
            var pe_doc_type = '';
        }

        if(pe_doc_type && vat) {
            if(!this.validate_pe_doc(pe_doc_type, vat)){
                await this.popup.add(ErrorPopup, {
                    title: _t("Error"),
                    body: _t("The document number is invalid."),
                });
                return ;
            }
            else if(['1', '6'].indexOf(pe_doc_type)!=-1){
                const result = await this.orm.call("res.partner", "get_partner_from_ui", [pe_doc_type, vat]);
                if (!result.detail && result.detail!="Not found."){
                    if (pe_doc_type == "1"){
                        self.changes['pe_is_validate'] = true;
                        self.changes['pe_last_update'] = result.last_update;
                        self.changes['name'] = result.paternal_surname+' '+result.maternal_surname+', '+ result.name;
                        self.changes['pe_is_validate'] = true;
                        self.changes['pe_last_update'] = result.last_update;
                    }
                    else if (pe_doc_type == "6"){
                        self.changes['name'] = result.legal_name;
                        self.changes['pe_commercial_name'] = result.commercial_name;
                        self.changes['pe_legal_name'] = result.legal_name;
                        self.changes['street'] = result.street;
                        self.changes['pe_is_validate'] = true;
                        self.changes['pe_last_update'] = result.last_update;
                        self.changes['pe_state'] = result.state;
                        self.changes['pe_condition'] = result.condition;
                        self.changes['city'] = result.city;
                        self.changes['state_id'] = result.state_id;
                        self.changes['city_id'] = result.city_id;
                        self.changes['l10n_pe_district'] = result.l10n_pe_district;
                        self.changes['zip'] = result.zip;
                    }
                }
            }
        }
    },
    validate_pe_doc(pe_doc_type, vat) {
        if (!pe_doc_type || !vat){
            return true;
        }
        var regex=/^[a-zA-Z0-9]+$/;
        if(!vat.match(regex)){
            return false;
        }
        if (pe_doc_type=='1') {
            regex=/^[0-9]{8}$/;
            if(vat.match(regex)){
                return true;
            }
            else{
                return false;
            }

        }
        else if (pe_doc_type=='6')
        {
            regex=/^[0-9]{11}$/;
            if(!vat.match(regex)){
                return false;
            }
            var vat= vat;
            var factor = '5432765432';
            var sum = 0;
            var dig_check = false;

            for (var i = 0; i < factor.length; i++) {
                sum += parseInt(factor[i]) * parseInt(vat[i]);
             }

            var subtraction = 11 - (sum % 11);
            if (subtraction == 10){
                dig_check = 0;
            }
            else if (subtraction == 11){
                dig_check = 1;
            }
            else{
                dig_check = subtraction;
            }

            if (parseInt(vat[10]) != dig_check){
                return false;
            }
            return true;
        }
        else {
            return true;
        }
    }
});


