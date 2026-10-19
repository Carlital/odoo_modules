odoo.define('l10n_pe_pos.models', function (require) {
"use strict";

var core = require('web.core');
var { PosGlobalState, Order, Orderline } = require('point_of_sale.models');
const Registries = require('point_of_sale.Registries');
var _t = core._t;

const PePosGlobalState = (PosGlobalState) => class PePosGlobalState extends PosGlobalState {
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.pe_doc_types = [
                    {'code': '0', 'name':'DOC.TRIB.NO.DOM.SIN.RUC'},
                    {'code': '1', 'name':'DNI'},
                    {'code': '4', 'name':'CARNET DE EXTRANJERIA'},
                    {'code': '6', 'name':'RUC'},
                    {'code': '7', 'name':'PASAPORTE'},
                    {'code': 'A', 'name':'CÉDULA DIPLOMÁTICA DE IDENTIDAD'}];
        this.pe_states = [
                    {'code': 'ACTIVO', 'name':'ACTIVO'},
                    {'code': 'BAJA DE OFICIO', 'name':'BAJA DE OFICIO'},
                    {'code': 'BAJA PROVISIONAL', 'name':'BAJA PROVISIONAL'},
                    {'code': 'SUSPENSION TEMPORAL', 'name':'SUSPENSION TEMPORAL'},
                    {'code': 'INHABILITADO-VENT.UN', 'name':'INHABILITADO-VENT.UN'},
                    {'code': 'BAJA MULT.INSCR. Y O', 'name':'BAJA MULT.INSCR. Y O'},
                    {'code': 'PENDIENTE DE INI. DE', 'name':'PENDIENTE DE INI. DE'},
                    {'code': 'OTROS OBLIGADOS', 'name':'OTROS OBLIGADOS'},
                    {'code': 'NUM. INTERNO IDENTIF', 'name':'NUM. INTERNO IDENTIF'},
                    {'code': 'ANUL.PROVI.-ACTO ILI', 'name':'ANUL.PROVI.-ACTO ILI'},
                    {'code': 'ANULACION - ACTO ILI', 'name':'ANULACION - ACTO ILI'},
                    {'code': 'BAJA PROV. POR OFICI', 'name':'BAJA PROV. POR OFICI'},
                    {'code': 'ANULACION - ERROR SU', 'name':'ANULACION - ERROR SU'},
                    ];
        this.pe_conditions = [
                    {'code': 'HABIDO', 'name':'HABIDO'},
                    {'code': 'NO HALLADO', 'name':'NO HALLADO'},
                    {'code': 'NO HABIDO', 'name':'NO HABIDO'},
                    {'code': 'PENDIENTE', 'name':'PENDIENTE'},
                    {'code': 'NO HALLADO SE MUDO D', 'name':'NO HALLADO SE MUDO D'},
                    {'code': 'NO HALLADO NO EXISTE', 'name':'NO HALLADO NO EXISTE'},
                    {'code': 'NO HALLADO FALLECIO', 'name':'NO HALLADO FALLECIO'},
                    {'code': 'NO HALLADO OTROS MOT', 'name':'NO HALLADO OTROS MOT'},
                    {'code': 'NO APLICABLE', 'name':'NO APLICABLE'},
                    {'code': 'NO HALLADO NRO.PUERT', 'name':'NO HALLADO NRO.PUERT'},
                    {'code': 'NO HALLADO CERRADO', 'name':'NO HALLADO CERRADO'},
                    {'code': 'POR VERIFICAR', 'name':'POR VERIFICAR'},
                    {'code': 'NO HALLADO DESTINATA', 'name':'NO HALLADO DESTINATA'},
                    {'code': 'NO HALLADO RECHAZADO', 'name':'NO HALLADO RECHAZADO'},
                    {'code': '-', 'name':'NO HABIDO'},
                    ];
    }

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
}

Registries.Model.extend(PosGlobalState, PePosGlobalState);

const PePosOrder = (Order) => class PePosOrder extends Order {
    constructor(obj, options) {
        super(...arguments);
    }
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
    }
    get_pe_doc_type() {
        var partner = this.get_partner();
        var pe_doc_type=partner ? partner.pe_doc_type : "";
        return pe_doc_type;
    }
    get_vat() {
        var partner = this.get_partner();
        var vat=partner ? partner.vat : "";
        return vat;
    }
    get_amount_text() {
        return numeroALetras(this.get_total_with_tax(), {
                                          plural: this.pos.currency.currency_unit_label,
                                          singular: this.pos.currency.currency_unit_label,
                                          centPlural: "",
                                          centSingular: ""
                                        })
    }
    get_pe_tax_details() {
        var basedetails = {};
        var taxdetails = {};

        var fullDetails = [];
        var subtotal = 0.0;

        var self = this;

        var taxbycode = {}

        this.orderlines.forEach(function(line){
            var taxes = line.get_pe_tax_details();
            if (taxes.length>0){
                for (var i = 0; i < taxes.length; i++) {
                    var tax = self.pos.taxes_by_id[taxes[i].id];
                    if(!basedetails.hasOwnProperty(tax.l10n_pe_edi_tax_code)){
                        basedetails[tax.l10n_pe_edi_tax_code] = 0.0;
                        taxdetails[tax.l10n_pe_edi_tax_code] = 0.0;
                        taxbycode[tax.l10n_pe_edi_tax_code] = tax;
                    }
                    basedetails[tax.l10n_pe_edi_tax_code] += taxes[i].base;
                    if (taxes[i].amount>0.0){
                        taxdetails[tax.l10n_pe_edi_tax_code] += taxes[i].amount;    
                    }
                }
            }
            
        });

        for(var code in basedetails) {
            var details = {};
            details['amount'] = basedetails[code];
            details['tax'] = taxbycode[code];
            if (code == '1000'){
                details['name'] = _t('GRAVADA');
            }
            else {
                details['name'] = taxbycode[code].description;
            }
            fullDetails.push(details);
        }
        for (var code in taxdetails) {
            var details = {};
            if (taxdetails[code]!=0.0){
                details['amount'] = taxdetails[code];
                details['tax'] = taxbycode[code];
                details['name'] = taxbycode[code].description;
                fullDetails.push(details);
            }
        }
        return fullDetails;
    }
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        if (!this.invoice_date){
            this.invoice_date = moment(new Date().getTime()).format('YYYY-MM-DD');
        }
        json.invoice_date = this.invoice_date;
        return json;
    }
    export_for_printing(){
        const json = super.export_for_printing(...arguments);
        let company = this.pos.company;
        if (!this.invoice_date){
            this.invoice_date = moment(new Date().getTime()).format('YYYY-MM-DD');
        }
        json.invoice_date = this.invoice_date;
        const company_json = json.company;
        company_json['l10n_pe_district'] = company.l10n_pe_district ? company.l10n_pe_district[1]: '';
        company_json['city_id'] = company.city_id ? company.city_id[1]: '';
        company_json['state_id'] = company.state_id ? company.state_id[1]: '';
        company_json['zip'] = company.zip || '';
        company_json['street'] = company.street || '';
        json.company = company_json;
        json['pe_tax_details'] = this.get_pe_tax_details();
        json['pe_amount_text'] = this.get_amount_text().toUpperCase();
        return json;
    }
}
Registries.Model.extend(Order, PePosOrder);


const PePosOrderline = (Orderline) => class PePosOrderline extends Orderline {

    get_pe_tax_details(){
        var prices = this.get_pe_all_prices()
        return prices.taxes;
    }
    get_pe_all_prices(){
        var qty = this.get_quantity();
        var price_unit = this.get_unit_price() * (1.0 - (this.get_discount() / 100.0));
        var taxtotal = 0;

        var product =  this.get_product();
        var taxes_ids = this.tax_ids || product.taxes_id;
        taxes_ids = _.filter(taxes_ids, t => t in this.pos.taxes_by_id);
        var taxdetail = {};
        var product_taxes = this.pos.get_taxes_after_fp(taxes_ids, this.order.fiscal_position);

        var all_taxes = this.compute_all(product_taxes, price_unit, qty, this.pos.currency.rounding);
        var all_taxes_before_discount = this.compute_all(product_taxes, this.get_unit_price(), qty, this.pos.currency.rounding);
        _(all_taxes.taxes).each(function(tax) {
            taxtotal += tax.amount;
            taxdetail[tax.id] = tax.amount;
        });

        return all_taxes;
    }
}
Registries.Model.extend(Orderline, PePosOrderline);


});
