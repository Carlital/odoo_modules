# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountJournal(models.Model):
    _inherit = "account.journal"
    
    pe_credit_note_id = fields.Many2one(comodel_name="account.journal", string="Credit Note", domain="[('type','in', ['sale', 'purchase'])]")
    pe_debit_note_id = fields.Many2one(comodel_name="account.journal", string="Debit Note", domain="[('type','in', ['sale', 'purchase'])]")
    pe_invoice_code = fields.Selection(selection="_get_pe_invoice_code", string="Invoice Type Code")
    pe_credit_invoice_code = fields.Selection(selection="_get_pe_invoice_code", string="Credit Invoice Type Code")
    pe_debit_invoice_code = fields.Selection(selection="_get_pe_invoice_code", string="Debit Invoice Type Code")
    
    pe_debit_sequence = fields.Boolean(string='Dedicated Debit Note Sequence', help="Check this box if you don't want to share the same sequence for invoices and debit notes made from this journal", default=False)

    
    @api.model
    def _get_pe_invoice_code(self):
        return self.env['pe.catalog.01'].get_selection()
    
    @api.onchange('pe_invoice_code')
    def _onchange_pe_invoice_code(self):
        if self.pe_invoice_code:
            if self.pe_invoice_code in ['01', '03']:
                self.pe_credit_invoice_code = '07'
                self.pe_debit_invoice_code = '08'
        return {}
    
    
    def write(self, vals):
        res = super(AccountJournal, self).write(vals)
        return res
        
    @api.model
    def create(self, vals):
        res = super(AccountJournal, self).create(vals)
        return res
    

class AccountTax(models.Model):
    _inherit = 'account.tax'

    pe_tax_type = fields.Many2one(comodel_name="pe.catalog.05", string="Tax Type",
                                  compute="_compute_pe_tax_type", store=True, readonly=False)
        
    pe_tier_range = fields.Selection(selection= "_get_pe_tier_range", string="Type of System", 
                                     help="Type of system to the ISC")
    
    pe_is_charge = fields.Boolean("Charge")

    def _compute_pe_tax_type(self):
        for tax in self:
            tax.pe_tax_type = self.env['pe.catalog.05'].search([('code', '=', tax.l10n_pe_edi_tax_code)], limit=1)

    @api.model
    def _get_pe_tier_range(self):
        return self.env['pe.catalog.08'].get_selection()
    
    @api.model
    def _get_pe_tax_code(self):
        return self.env['pe.catalog.05'].get_selection()
    
    @api.onchange('pe_tax_type')
    def onchange_pe_tax_type(self):
        if self.pe_tax_type:
            self.l10n_pe_edi_tax_code = self.pe_tax_type.code
            #self.l10n_pe_edi_unece_category = self.pe_tax_type.un_ece_code
            self.description = self.pe_tax_type.name_code
        else:
            self.l10n_pe_edi_tax_code = False