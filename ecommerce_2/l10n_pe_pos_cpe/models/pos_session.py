# -*- coding: utf-8 -*-

from odoo import models, api

class PosSession(models.Model):
    _inherit = 'pos.session'

    # @api.model
    # def _pos_ui_models_to_load(self):
    #     result = super()._pos_ui_models_to_load()
    #     journal_model = 'account.journal'
    #     if journal_model not in result:
    #         result.append(journal_model)
    #     return result

    # def _loader_params_account_journal(self):
    #     journal_ids = self.config_id.pe_default_journal_ids.ids
    #     return {'search_params': {'domain': [('id','in',journal_ids)], 'fields': ['name','pe_invoice_code',
    #                                                        'pe_sequence_prefix',
    #                                                        'pe_sequence_number',
    #                                                        'pe_padding',
    #                                                        'pe_is_cpe', 'pe_credit_note_id']}}
    #
    # def _get_pos_ui_account_journal(self, params):
    #     return self.env['account.journal'].search_read(**params['search_params'])
    #
    # def _loader_params_res_company(self):
    #     res = super()._loader_params_res_company()
    #     fields = res.get('search_params', {}).get('fields', [])
    #     fields += ["pe_max_amount"]
    #     res['search_params']['fields'] = fields
    #     return res

    @api.model
    def _load_pos_data_models(self, config_id):
        data = super()._load_pos_data_models(config_id)
        if self.env.company.country_id.code == "PE":
            data += ['account.journal']
        return data

    def _load_pos_data(self, data):
        data = super()._load_pos_data(data)
        if self.env.company.country_id.code == "PE":
            data_fields = ['name','pe_invoice_code', 'pe_sequence_prefix', 'pe_sequence_number', 'pe_padding', 'pe_is_cpe', 'pe_credit_note_id']
            journals = self.env['account.journal'].search_read([('id', 'in', self.config_id.pe_default_journal_ids.ids)], fields=data_fields)
            pe_journal_by_id = {journal['id']: journal for journal in journals}
            pe_journal_by_pe_invoice_code = {journal['pe_invoice_code']: journal for journal in journals}
            data['data'][0]['_pe_journal_by_id'] = pe_journal_by_id
            data['data'][0]['_pe_journal_by_pe_invoice_code'] = pe_journal_by_pe_invoice_code
            data['data'][0]['_pe_journal_ids'] = self.config_id.pe_journal_ids.ids
            data['data'][0]['_pe_default_journal_ids'] = journals
        return data