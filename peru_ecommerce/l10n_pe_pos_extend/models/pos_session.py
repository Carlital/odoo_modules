# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api
class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_res_company(self):
        res = super()._loader_params_res_company()
        fields = res.get('search_params', {}).get('fields', [])
        fields += ["state_id", "zip", "street", "city_id", "l10n_pe_district"]
        res['search_params']['fields'] = fields
        return res

    def _loader_params_res_currency(self):
        res = super()._loader_params_res_currency()
        fields = res.get('search_params', {}).get('fields', [])
        fields += ["currency_unit_label", "currency_subunit_label"]
        res['search_params']['fields'] = fields
        return res

    def _loader_params_account_tax(self):
        res = super()._loader_params_account_tax()
        fields = res.get('search_params', {}).get('fields', [])
        fields += ["description", "l10n_pe_edi_tax_code", "invoice_label"]
        res['search_params']['fields'] = fields
        return res

    def _loader_params_l10n_latam_identification_type(self):
        res = super()._loader_params_l10n_latam_identification_type()
        fields = res.get('search_params', {}).get('fields', [])
        fields += ["l10n_pe_vat_code"]
        res['search_params']['fields'] = fields
        return res