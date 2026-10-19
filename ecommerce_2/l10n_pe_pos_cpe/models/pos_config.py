# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class PosConfig(models.Model):
    _inherit = 'pos.config'
    
    pe_auto_journal_select = fields.Boolean("Auto Journal Select", help="Automatically select the journal")
    pe_force_journal_select = fields.Boolean("Force Journal Select", help="Force select the journal")
    pe_journal_ids = fields.Many2many("account.journal", string="Invoice Sale Journals",
                                      domain="[('type', 'in', ['sale']),('company_id', '=', company_id)]")
    
    pe_default_journal_ids = fields.Many2many("account.journal", string="Invoice Sale Journals", compute = '_compute_pe_default_journal_ids')

    def _compute_pe_default_journal_ids(self):
        for config in self:
            journal_ids = []
            for journal_id in config.pe_journal_ids:
                journal_ids.append(journal_id.id)
                if journal_id.pe_credit_note_id:
                    journal_ids.append(journal_id.pe_credit_note_id.id)
            config.pe_default_journal_ids = journal_ids