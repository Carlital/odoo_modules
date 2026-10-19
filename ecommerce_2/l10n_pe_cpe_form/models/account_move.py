# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = "account.move"

    pe_edi_zip = fields.Many2one('ir.attachment', "EDI ZIP", compute="_compute_pe_edi_zip")

    def _compute_pe_edi_zip(self):
        for move in self:
            edi_attachment_zipped = move._get_edi_attachment(self.env.ref('l10n_pe_edi.edi_pe_ubl_2_1'))
            move.pe_edi_zip = edi_attachment_zipped.id if edi_attachment_zipped else False
