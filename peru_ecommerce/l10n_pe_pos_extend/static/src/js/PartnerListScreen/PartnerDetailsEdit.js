odoo.define('l10n_pe_pos.PosResPartnerDetailsEdit', function (require) {
    'use strict';
    const { _t } = require('web.core');
    const PartnerDetailsEdit = require('point_of_sale.PartnerDetailsEdit');
    const Registries = require('point_of_sale.Registries');
    const rpc = require('web.rpc');
    const { onMounted, useState, onWillUnmount } = owl;

    const PosResPartnerDetailsEdit = (PartnerDetailsEdit) =>
        class extends PartnerDetailsEdit {
            constructor() {
                super(...arguments);
            }
            setup() {
                super.setup();
                const partner = this.props.partner;
                this.changes['pe_doc_type'] = partner.pe_doc_type || "";
                this.changes['pe_state'] = partner.pe_state || "";
                this.changes['pe_condition'] = partner.pe_condition || "";
            }
            captureChange(event){
                super.captureChange(event);
                var pe_doc_type = this.changes['pe_doc_type'];
                var vat = this.changes['vat']
                var self = this;
                if (this.changes['pe_doc_type']=='6') {
                    $('.partner-pe-condition').show();
                    $('.partner-pe-state').show();
                    
                } else {
                    $('.partner-pe-condition').hide();
                    $('.partner-pe-state').hide();
                }
                if(this.changes['pe_doc_type'] && this.changes['vat']) {
                    if(!this.env.pos.validate_pe_doc(pe_doc_type, vat)){
                        return this.showPopup('ErrorPopup', {
                          title: _t('The document number is invalid'),
                        });
                    }
                    else if(['1', '6'].indexOf(pe_doc_type)!=-1){
                        rpc.query({
                        model: 'res.partner',
                        method: 'get_partner_from_ui',
                        args: [pe_doc_type, vat],
                        }, {
                            timeout: 7500,
                        })
                        .then(function (result) {
                            if (result.detail!="Not found."){
                                if (pe_doc_type == "1"){
                                    $("[name='name']").val(result.paternal_surname+' '+result.maternal_surname+', '+ result.name);
                                    $('.pe_is_validate').val(true);//attr('checked', true);
                                    $('.pe_last_update').val(result.last_update);
                                    self.changes['name'] = result.paternal_surname+' '+result.maternal_surname+', '+ result.name;
                                    self.changes['pe_is_validate'] = true;
                                    self.changes['pe_last_update'] = result.last_update;
                                }
                                else if (pe_doc_type == "6"){
                                    $("[name='name']").val(result.legal_name);
                                    $('.pe_commercial_name').val(result.commercial_name);
                                    $('.pe_legal_name').val(result.legal_name);
                                    $("[name='street']").val(result.street);
                                    $('.pe_is_validate').val(true);//attr('checked', true);
                                    //self.$('.vat').val(vat);
                                    $('.pe_last_update').val(result.last_update);
                                    $("[name='pe_state']").val(result.state);
                                    $("[name='pe_condition']").val(result.condition);

                                    $("[name='city']").val(result.city);
                                    $("[name='state_id']").val(result.state_id);
                                    $("[name='l10n_pe_district']").val(result.l10n_pe_district);
                                    $("[name='zip']").val(result.zip);

                                    $("[name='city_id']").val(result.city_id);
                                    
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
                                    self.changes['l10n_pe_district'] = result.l10n_pe_district;
                                    self.changes['zip'] = result.zip;
                                }
                            }
                        }).catch(function (error){
                            console.log('Failed to get partner:');
                        });
                    }
                }
            }
        
        };

    Registries.Component.extend(PartnerDetailsEdit, PosResPartnerDetailsEdit);

    return PosResPartnerDetailsEdit;
});
