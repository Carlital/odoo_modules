# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import re

class AccountJournal(models.Model):
    _name = "account.journal"
    _inherit = ['account.journal', 'pos.load.mixin']

    pe_sequence_prefix = fields.Char(compute='_compute_pe_sequence')
    pe_sequence_number = fields.Integer(compute='_compute_pe_sequence')
    pe_padding = fields.Integer(compute='_compute_pe_sequence')
    pe_is_cpe = fields.Boolean(compute = '_compute_pe_is_cpe')
    
    @api.depends('edi_format_ids')
    def _compute_pe_is_cpe(self):
        for journal_id in self:
            journal_id.pe_is_cpe = bool(journal_id.edi_format_ids.filtered(lambda j: j.code == 'pe_cpe'))
    
    def _compute_pe_sequence(self):
        for journal_id in self:
            vals = journal_id._get_pe_sequence()
            journal_id.pe_sequence_prefix = vals[journal_id.id].get('pe_sequence_prefix', False)
            journal_id.pe_sequence_number = vals[journal_id.id].get('pe_sequence_number', False)
            journal_id.pe_padding = vals[journal_id.id].get('pe_padding', False)

    
    def _get_pe_sequence(self):
        sequence_vals = {}
        for journal_id in self:
            move_id = self.env['account.move'].search([('journal_id','=',journal_id.id),('name','!=','/'),('state','!=','draft')], order='name DESC', limit = 1)
            vals = {}
            if move_id and re.findall(r'^.*([A-Z0-9]{4})-(\d{1,8})$', move_id.name):
                check_move_name = re.findall(r'^.*([A-Z0-9]{4})-(\d{1,8})$', move_id.name)
                vals['pe_sequence_prefix'] = "%s-" % (check_move_name[0][0] or '')
                vals['pe_sequence_number'] = int(check_move_name[0][1]) or 0
                vals['pe_padding'] = 8
            else:
                vals['pe_sequence_prefix'] = "%s-" % (journal_id.code or '')
                vals['pe_sequence_number'] = 0
                vals['pe_padding'] = 8
            sequence_vals[journal_id.id] = vals
        return sequence_vals
    
    def get_pe_sequence(self):
        return self._get_pe_sequence()

    @api.model
    def _load_pos_data_domain(self, data):
        domain = super()._load_pos_data_domain(data)
        pe_default_journal_ids = self.env['pos.config'].browse(data['pos.config']['data'][0]['id']).pe_default_journal_ids.ids
        if pe_default_journal_ids:
            domain += [('id', 'in', pe_default_journal_ids)]
        return domain

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields = super()._load_pos_data_fields(config_id)
        fields += ['name','pe_invoice_code', 'pe_sequence_prefix', 'pe_sequence_number', 'pe_padding',
                   'pe_is_cpe', 'pe_credit_note_id']
        return fields

    # def _load_pos_data(self, data):
    #     res = super()._load_pos_data(data)
    #     return res