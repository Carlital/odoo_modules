# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PeCpeCorrect(models.TransientModel):
    _name = "pe.cpe.correct.wizard"
    
    @api.model
    def _get_default_cpe_id(self):
        return self.env.context.get('active_id')

    cpe_id = fields.Many2one("pe.cpe.rc", "CPE", default= _get_default_cpe_id)
    invoice_ids = fields.Many2many("account.move",
                                   string="Invoices")
    is_new = fields.Boolean("New")
    add_invoice = fields.Boolean("Add Invoice")
    summary_invoice_ids = fields.Many2many("account.move", string="Summaries", compute="_compute_summary_invoice_ids")

    @api.depends('cpe_id')
    def _compute_summary_invoice_ids(self):
        for record in self:
            record.summary_invoice_ids = record.cpe_id.summary_ids

    def correct_invoices(self):
        self.ensure_one()
        if self.is_new:
            self.cpe_id.write({'name':'/'})
        if not self.add_invoice:
            self.cpe_id.summary_ids.write({'pe_condition_code':'1'})
        self.invoice_ids.write({'pe_condition_code':'2'})
        for invoice_id in self.cpe_id.summary_ids.filtered(lambda s: s.pe_annul):
            pe_summary_id=self.env['pe.cpe.rc'].get_cpe_async("rc", invoice_id.id, True)
            invoice_id.pe_summary_id=pe_summary_id.id
            invoice_id.pe_condition_code = '3'
        self.cpe_id.pe_response = False
        self.cpe_id.pe_response_code = False
        self.cpe_id.pe_note = False
        self.cpe_id.pe_return_code = False
        self.cpe_id.pe_ticket = False
        self.cpe_id.attachment_id.unlink()
        self.cpe_id.pe_response_id.unlink()
        self.cpe_id.state = 'to_send'
        return {}