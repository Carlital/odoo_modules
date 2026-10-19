# -*- coding: utf-8 -*-

from odoo import models, api

class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.model
    def _pos_ui_models_to_load(self):
        result = super()._pos_ui_models_to_load()
        journal_model = 'account.journal'
        if journal_model not in result:
            result.append(journal_model)
        return result

    def _loader_params_account_journal(self):
        journal_ids = self.config_id.pe_default_journal_ids.ids
        return {'search_params': {'domain': [('id','in',journal_ids)], 'fields': ['name','pe_invoice_code',
                                                           'pe_sequence_prefix',
                                                           'pe_sequence_number',
                                                           'pe_padding',
                                                           'pe_is_cpe', 'pe_credit_note_id']}}

    def _get_pos_ui_account_journal(self, params):
        return self.env['account.journal'].search_read(**params['search_params'])

    # def _loader_params_res_partner(self):
    #     res = super()._loader_params_res_partner()
    #     fields = res.get('search_params', {}).get('fields', [])
    #     fields += ["pe_doc_type", "pe_commercial_name", "pe_legal_name", "pe_is_validate", "pe_state", "pe_condition"]
    #     res['search_params']['fields'] = fields
    #     return res

    def _loader_params_res_company(self):
        res = super()._loader_params_res_company()
        fields = res.get('search_params', {}).get('fields', [])
        fields += ["pe_max_amount"]
        res['search_params']['fields'] = fields
        return res
