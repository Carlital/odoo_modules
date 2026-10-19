# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountJournal(models.Model):
    _inherit = "account.journal"

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
            move_id = self.env['account.move'].search([('journal_id','=',journal_id.id),('name','!=','/')], order='name DESC', limit = 1)
            vals = {}
            if move_id:
                vals['pe_sequence_prefix'] = "%s-" % (move_id.pe_prefix or '')
                vals['pe_sequence_number'] = move_id.pe_number or 0
                vals['pe_padding'] = 8
            else:
                vals['pe_sequence_prefix'] = "%s-" % (journal_id.code or '')
                vals['pe_sequence_number'] = 0
                vals['pe_padding'] = 8
            sequence_vals[journal_id.id] = vals
        return sequence_vals
    
    def get_pe_sequence(self):
        return self._get_pe_sequence()