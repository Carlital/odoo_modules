# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError


class AccountDebitNote(models.TransientModel):
    _inherit = 'account.debit.note'
    
    pe_debit_note_code = fields.Selection(selection="_get_pe_debit_note_type", string="Dedit Note Code")
    
    @api.model
    def _get_pe_debit_note_type(self):
        return self.env['pe.catalog.10'].get_selection()
    
    def _prepare_default_values(self, move):
        default_values = super(AccountDebitNote, self)._prepare_default_values(move)
        default_values['pe_debit_note_code'] = self.pe_debit_note_code
        # l10n_latam_document_type_id = self.env['l10n_latam.document.type'].search(
        #     [('code', '=', '08', 'prefix', '=', move.l10n_latam_document_type_id.prefix)], limit=1).id
        # if l10n_latam_document_type_id:
        #     default_values['l10n_latam_document_type_id'] = l10n_latam_document_type_id
        if not move.journal_id.pe_debit_note_id:
            default_values['journal_id'] = move.journal_id.pe_debit_note_id.id
        default_values['date'] = move.invoice_date
        default_values['invoice_origin'] = move.name
        return default_values