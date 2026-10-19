# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMoveReversal(models.TransientModel):

    _inherit = 'account.move.reversal'
    
    pe_credit_note_code = fields.Selection(selection="_get_pe_credit_note_type", string="Credit Note Code")
    
    @api.model
    def _get_pe_credit_note_type(self):
        return self.env['pe.catalog.09'].get_selection()
    
    def _prepare_default_reversal(self, move):
        res = super(AccountMoveReversal, self)._prepare_default_reversal(move=move)
        res['ref'] = self.reason
        res['pe_credit_note_code'] = self.pe_credit_note_code
        # l10n_latam_document_type_id = self.env['l10n_latam.document.type'].search(
        #     [('code', '=', '07', 'prefix', '=', move.l10n_latam_document_type_id.prefix)], limit=1).id
        # if l10n_latam_document_type_id:
        #     res['l10n_latam_document_type_id'] = l10n_latam_document_type_id
        if move.journal_id.pe_credit_note_id:
            res['journal_id'] = move.journal_id.pe_credit_note_id.id
        res['invoice_origin'] = move.name
        res['date'] = move.invoice_date
        return res