# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from functools import lru_cache
import re

class AccountMove(models.Model):
    _inherit = "account.move"
    
    pe_invoice_code = fields.Selection(selection="_get_pe_invoice_code", string="Invoice Type Code", compute = "_compute_pe_invoice_code",
                                       store=True)
    pe_debit_note_code = fields.Selection(selection="_get_pe_debit_note_type", string="Dedit Note Code")
    pe_credit_note_code = fields.Selection(selection="_get_pe_credit_note_type", string="Credit Note Code")
    pe_license_plate = fields.Char("License Plate", size=10)
    
    pe_qty_fees = fields.Integer("Fees", default = 1)

    pe_payment_lines = fields.One2many('pe.payment.date', 'move_id', 'Payment Lines')
    
    pe_annul = fields.Boolean('Annulled', readonly=True, copy = False)

    pe_subject_detraction = fields.Selection('_get_pe_subject_detraction', 'Subject to Detraction')
    pe_detraction_amount = fields.Monetary('Detraction Amount', copy=False, store = True, currency_field='company_currency_id',
                                           compute="_compute_pe_detraction_amount_percentage")
    pe_detraction_percentage = fields.Float('Detraction Percentage', digits=(12, 2), copy=False, store = True,
                                            compute="_compute_pe_detraction_amount_percentage")

    pe_subject_retention = fields.Selection("_get_pe_subject_retention", "Subject to Retention")
    pe_retention_percentage = fields.Float('Retention Percentage', digits=(12, 2), copy=False, store=True,
                                            compute="_compute_pe_retention_amount_percentage")
    pe_retention_amount = fields.Monetary('Retention Amount', copy=False, store=True,
                                           compute="_compute_pe_retention_amount_percentage")

    pe_discount_type = fields.Selection([('percentage','Percentage'),
                                         ('fixed', 'Fixed')], "Discount", default='fixed')
    pe_discount_percentage = fields.Float('Discount Percentage', digits=(12, 5), inverse = '_inverse_pe_discount',
                                           compute="_compute_pe_discount")
    pe_discount_amount = fields.Monetary('Discount Amount', inverse = '_inverse_pe_discount',
                                           compute="_compute_pe_discount")

    pe_amount_to_paid = fields.Monetary("Amount to Paid after detraction o Retention",
                                        compute="_compute_pe_amount_to_paid")
    pe_prefix = fields.Char("Prefix", compute="_compute_pe_prefix_number", store=True)
    pe_number = fields.Integer("Number", compute="_compute_pe_prefix_number", store=True)

    @api.depends('name', 'state')
    def _compute_pe_prefix_number(self):
        for move in self.filtered(lambda s: s.name != '/' and s.country_code=='PE' and s.state != 'draft'):
            check_move_name = move.name and re.findall(r'^.*([A-Z0-9]{4})-(\d{1,8})$', move.name) or False
            if check_move_name:
                move.pe_prefix = check_move_name[0][0]
                move.pe_number = int(check_move_name[0][1])
            else:
                move.pe_prefix = False
                move.pe_number = False

    @api.depends('l10n_latam_document_type_id')
    def _compute_pe_invoice_code(self):
        for move in self:
            if move.l10n_latam_document_type_id.country_id.code == 'PE':
                move.pe_invoice_code = move.l10n_latam_document_type_id.code
            else:
                move.pe_invoice_code = False

    def _compute_pe_amount_to_paid(self):
        for move_id in self.filtered(lambda s: s.country_code=='PE'):
            total = 0.0
            if move_id.pe_subject_detraction and move_id.pe_detraction_amount > 0.0:
                catalog_id = self.env['pe.catalog.54'].get_by_code(move_id.pe_subject_detraction)
                pe_detraction_percentage = round(catalog_id.rate / 100, 2)
                move_id.pe_detraction_percentage = pe_detraction_percentage
                total += pe_detraction_percentage * move_id.amount_total
            if move_id.pe_retention_amount > 0.0:
                total += move_id.pe_retention_amount
            move_id.pe_amount_to_paid = move_id.amount_total - total

    @api.depends('pe_discount_type', 'pe_discount_percentage', 'pe_discount_amount', 'pe_discount_type', 'invoice_line_ids',
                 'invoice_line_ids.price_total')
    def _compute_pe_discount(self):
        for move_id in self.filtered(lambda s: s.country_code=='PE'):
            if move_id.pe_discount_type:
                pe_discount_amount = abs(sum(move_id.invoice_line_ids.filtered(lambda s: s.pe_is_discount==True).mapped('price_total')))
                if move_id.pe_discount_type in ['fixed']:
                    if not move_id.pe_discount_amount and pe_discount_amount:
                        move_id.pe_discount_amount = pe_discount_amount
                    move_id.pe_discount_percentage = move_id.amount_total>0.0 and pe_discount_amount*100/(move_id.amount_total + pe_discount_amount) or 0.0
                elif move_id.pe_discount_type in ['percentage']:
                    if not move_id.pe_discount_percentage and pe_discount_amount:
                        move_id.pe_discount_percentage = move_id.amount_total>0.0 and pe_discount_amount*100/(move_id.amount_total + pe_discount_amount) or 0.0
                    move_id.pe_discount_amount = move_id.amount_total>0.0 and (move_id.amount_total + pe_discount_amount)  * move_id.pe_discount_percentage / 100 or 0.0
            else:
                move_id.pe_discount_amount = 0.0

    def _inverse_pe_discount(self):
        for move_id in self:
            if move_id.pe_discount_type:
                move_id.sudo().invoice_line_ids.filtered(lambda s: s.pe_is_discount==True).unlink()
                if not move_id.pe_discount_amount:
                    continue
                product_id = self.env['product.product'].search([('pe_product_type','=','discount')], limit=1)
                fiscal_position = move_id.fiscal_position_id
                accounts = product_id.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
                account_id = False
                if move_id.is_sale_document(include_receipts=True):
                    account_id = accounts['income']
                elif move_id.is_purchase_document(include_receipts=True):
                    account_id = accounts['expense']
                vals = {}
                vals['name'] = product_id.name or _("Global Discount")
                vals['product_id'] = product_id.id
                vals['account_id'] = account_id and account_id.id or move_id.journal_id.default_account_id.id
                vals['quantity'] = 1
                vals['discount'] = 0
                vals['price_unit'] = -move_id.pe_discount_amount
                vals['tax_ids'] = product_id and product_id.taxes_id.ids or []
                vals['currency_id'] = move_id.currency_id.id
                # vals['recompute_tax_line'] = True
                vals['pe_is_discount'] = True
                vals['move_id'] = move_id.id
                vals['pe_type_affectation'] = self.env['account.move.line'].get_pe_type_affectation_by_tax(
                    product_id.taxes_id)
                move_id.with_context(check_move_validity=False).invoice_line_ids.create(vals)
                move_id._onchange_currency()
                move_id._recompute_dynamic_lines(recompute_all_taxes=True)

    @api.model
    def _get_pe_subject_retention(self):
        return self.env['pe.catalog.23'].get_selection()

    @api.depends('pe_subject_retention', 'amount_total', 'invoice_date')
    def _compute_pe_retention_amount_percentage(self):
        for move_id in self.filtered(lambda s: s.country_code=='PE'):
            amount = move_id.currency_id._convert(move_id.amount_total,
                                               move_id.env.ref('base.PEN'), move_id.company_id,
                                               move_id.invoice_date or fields.Date.context_today(self))
            if move_id.pe_subject_retention and amount>=700:
                catalog_id = self.env['pe.catalog.23'].get_by_code(move_id.pe_subject_retention)
                move_id.pe_retention_amount = catalog_id.percent * move_id.amount_total/100
                move_id.pe_retention_percentage = catalog_id.percent/100
            else:
                move_id.pe_retention_amount = 0.0
                move_id.pe_retention_percentage = 0.0

    @api.model
    def _get_pe_subject_detraction(self):
        return self.env['pe.catalog.54'].get_selection()

    @api.depends("pe_subject_detraction", "amount_total", "invoice_date", "currency_id")
    def _compute_pe_detraction_amount_percentage(self):
        for move_id in self.filtered(lambda s: s.country_code=='PE'):
            amount_total = move_id.currency_id._convert(move_id.amount_total,
                                               self.env.ref('base.PEN'), move_id.company_id,
                                               move_id.invoice_date or fields.Date.context_today(self))
            if move_id.pe_subject_detraction and amount_total>=700:
                catalog_id = self.env['pe.catalog.54'].get_by_code(move_id.pe_subject_detraction)
                pe_detraction_percentage = round(catalog_id.rate / 100, 2)
                move_id.pe_detraction_percentage = pe_detraction_percentage
                amount = move_id.currency_id._convert(pe_detraction_percentage * move_id.amount_total,
                                                      self.env.ref('base.PEN'), move_id.company_id,
                                                      move_id.invoice_date or fields.Date.context_today(self))
                move_id.pe_detraction_amount = amount
            else:
                move_id.pe_detraction_percentage = 0.0
                move_id.pe_detraction_amount = 0.0

    def prepare_pe_fees_vals(self):
        self.ensure_one()
        pe_start_date = self.invoice_date_due or fields.Date.context_today(self)
        pe_payment_date_start = pe_start_date
        pe_payment_date_end = self.needed_terms and max(
                (k['date_maturity'] for k in self.needed_terms.keys() if k),
                default=False,
            ) or self.invoice_date_due or fields.Date.context_today(self)
        vals = {}
        vals['pe_payment_date_start'] = pe_payment_date_start
        vals['pe_payment_date_end'] = pe_payment_date_end
        vals['pe_payment_qty'] = self.pe_qty_fees
        pe_detraction_amount = self.env.ref('base.PEN')._convert(self.pe_detraction_amount,
                                              self.currency_id, self.company_id,
                                              self.invoice_date or fields.Date.context_today(self))

        vals['pe_payment_amount'] = self.amount_total - (pe_detraction_amount + self.pe_retention_amount)
        return vals


    def generate_pe_fees(self):
        self.ensure_one()
        if self.pe_qty_fees<=0:
            raise ValidationError(_("The quotas must be greater than zero?"))
        elif self.amount_total <= 0.0:
            raise ValidationError(_("The total must be greater than zero "))
        if (self.invoice_date and self.invoice_date_due) and (self.invoice_date == self.invoice_date_due):
            raise ValidationError(_("The invoice date must be different from the due date"))
        vals = self.prepare_pe_fees_vals()
        self.pe_payment_lines.unlink()
        pe_payment_lines = self.env['pe.payment.date'].get_payment_by_qty_date(vals)
        self.pe_payment_lines = pe_payment_lines

    def _recompute_dynamic_lines(self, recompute_all_taxes=False, recompute_tax_base_amount=False):
        res = super(AccountMove, self)._recompute_dynamic_lines(recompute_all_taxes=recompute_all_taxes,
                                                                recompute_tax_base_amount=recompute_tax_base_amount)
        if self.env.context.get('pe_recompute_tax_base_amount'):
            for move_id in self:
                move_id.with_context(pe_recompute_tax_base_amount=False)._onchange_currency()
        return res
    
    def button_pe_annul(self):
        self = self.with_context(pe_annul_document = True)
        self.button_draft()
        self.write({'pe_annul':True})
        self.button_cancel()
        return True

    def button_draft(self):
        res = super(AccountMove, self).button_draft()
        self.write({'pe_annul':False})
        return res
    
    @api.model
    def _get_pe_debit_note_type(self):
        return self.env['pe.catalog.10'].get_selection()
    
    @api.model
    def _get_pe_credit_note_type(self):
        return self.env['pe.catalog.09'].get_selection()
    
    @api.model
    def _get_pe_invoice_code(self):
        return self.env['pe.table.10'].get_selection()
    
    def _post(self, soft=True):
        for move in self:
            if move.move_type  in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund'] and not move.pe_invoice_code:
                reversed_entry_id = move.reversed_entry_id
                if reversed_entry_id and reversed_entry_id.move_type in ['out_invoice','in_invoice'] and move.move_type in ['out_refund', 'in_refund']:
                    move.pe_invoice_code = '07'
                elif reversed_entry_id and reversed_entry_id.move_type in ['out_invoice','in_invoice'] and move.move_type in ['out_invoice', 'in_invoice']:
                    move.pe_invoice_code = '08'
                elif reversed_entry_id and reversed_entry_id.move_type in ['out_refund','in_refund'] and move.move_type in ['out_invoice', 'in_invoice']:
                    move.pe_invoice_code = '08'
                elif not reversed_entry_id:                            
                    if move.partner_id.pe_doc_type == '6':
                        move.pe_invoice_code = '01'
                    else:
                        move.pe_invoice_code = '03'
            # if not move.invoice_date:
            #     if move.is_sale_document(include_receipts=True):
            #         move.invoice_date = fields.Date.context_today(self)
            #         # move.with_context(check_move_validity=False)._onchange_invoice_date()
            #         date_due = move.invoice_date_due or fields.Date.context_today(self)
            #         date_invoice = move.invoice_date or fields.Date.context_today(self)
            #         if (date_due - date_invoice).days>0 and not move.pe_payment_lines:
            #             move.generate_pe_fees()
            #         elif (date_due - date_invoice).days<=0 and move.pe_payment_lines:
            #             move.pe_payment_lines.unlink()
        res = super(AccountMove, self)._post(soft=soft)
        return res
    
    def _get_pe_default_journal(self):
        self.ensure_one()
        if self.pe_invoice_code:
            journal = self.journal_id
            type = journal.type
            journal_id = False
            if type == 'sale':
                journal_id = self.env.user.pe_journal_ids.filtered(lambda s: s.pe_invoice_code == self.l10n_latam_document_type_id.code and s.company_id == self.company_id)
            if not journal_id:
                journal_id = self.env['account.journal'].search([('pe_invoice_code','=',self.l10n_latam_document_type_id.code),
                                                                 ('type','=',type),
                                                                 ('company_id','=',self.company_id.id)], limit = 1)
            self.journal_id = journal_id and journal_id.id or journal.id
    
    # @api.depends('l10n_latam_available_document_type_ids', 'debit_origin_id', 'partner_id')
    # def _compute_l10n_latam_document_type(self):
    #     recs = self.filtered(lambda x: x.state == 'draft' and x.company_id.country_id.code=='PE')
    #     super(AccountMove, self-recs)._compute_l10n_latam_document_type()
    #     for rec in recs:
    #         invoice_type = rec.move_type
    #         if rec.partner_id:
    #             if invoice_type in ['in_refund', 'out_refund']:
    #                 if rec.partner_id.pe_doc_type == '6':
    #                     rec.l10n_latam_document_type_id = self.env.ref('l10n_pe.document_type07')
    #                 else:
    #                     rec.l10n_latam_document_type_id = self.env.ref('l10n_pe.document_type07b')
    #             else:
    #                 if rec.partner_id.pe_doc_type == '6' and not rec.debit_origin_id:
    #                     rec.l10n_latam_document_type_id = self.env.ref('l10n_pe.document_type01')
    #                 elif rec.partner_id.pe_doc_type not in ['6'] and not rec.debit_origin_id:
    #                     rec.l10n_latam_document_type_id = self.env.ref('l10n_pe.document_type02')
    #                 elif rec.debit_origin_id:
    #                     rec.l10n_latam_document_type_id = self.env.ref('l10n_pe.document_type08')
    #         else:
    #             document_types = rec.l10n_latam_available_document_type_ids._origin
    #             if invoice_type in ['out_refund', 'in_refund']:
    #                 document_types = document_types.filtered(lambda x: x.internal_type not in ['debit_note', 'invoice'])
    #             elif invoice_type in ['out_invoice', 'in_invoice']:
    #                 document_types = document_types.filtered(lambda x: x.internal_type not in ['credit_note'])
    #             if rec.debit_origin_id:
    #                 document_types = document_types.filtered(lambda x: x.internal_type == 'debit_note')
    #             rec.l10n_latam_document_type_id = document_types and document_types[0].id
    
    # @api.onchange('partner_id')
    # def _onchange_partner_id(self):
    #     res = super(AccountMove, self)._onchange_partner_id()
    #     if self.move_type in ['out_invoice', 'in_invoice', 'in_refund', 'out_refund'] and self.country_code=='PE':
    #         if self.partner_id:
    #             if self.move_type in ['in_refund', 'out_refund']:
    #                 self.pe_invoice_code = '07'
    #             else:
    #                 if self.partner_id.pe_doc_type == '6' and self.pe_invoice_code not in ['01','08'] and not self.debit_origin_id:
    #                     self.pe_invoice_code = '01'
    #                 elif self.partner_id.pe_doc_type not in ['6'] and self.pe_invoice_code not in ['03','08'] and not self.debit_origin_id:
    #                     self.pe_invoice_code = '03'
    #                 elif self.debit_origin_id:
    #                     self.pe_invoice_code = '08'
    #         self._get_pe_default_journal()
    #     return res
    
    @api.onchange('l10n_latam_document_type_id')
    def _onchange_l10n_latam_document_type_id(self):
        res = super(AccountMove, self)._onchange_l10n_latam_document_type_id()
        self._get_pe_default_journal()
        return res

    @api.depends('invoice_date', 'company_id', 'reversed_entry_id', 'debit_origin_id')
    def _compute_date(self):
        res = super()._compute_date()
        country_id = self.env.ref('base.pe')
        for move in self.filtered(lambda s: s.company_id.country_id == country_id and s.is_invoice()):
            if move.reversed_entry_id:
                move.date = move.reversed_entry_id.date
            elif move.debit_origin_id:
                move.date = move.debit_origin_id.date
            if move.debit_origin_id or move.reversed_entry_id:
                self.env.add_to_compute(self._fields['name'], move)
        return res
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    pe_license_plate = fields.Char("License Plate", size=10)
    pe_type_affectation = fields.Selection(selection="_get_pe_type_affectation", string="Type of affectation",
                                           compute='_compute_pe_type_affectation', store=True, readonly=False)
    pe_is_discount = fields.Boolean("Is Discount")
    pe_prepaid_invoice_id = fields.Many2one("account.move", "Prepaid Payment")

    @api.depends('tax_ids')
    def _compute_pe_type_affectation(self):
        for line in self:
            pe_type_affectation = line._get_pe_type_affectation_by_tax()
            if pe_type_affectation == '11' and line.pe_type_affectation in ['12', '13', '14', '15', '16', '17']:
                #line.pe_type_affectation = pe_type_affectation
                continue
            elif pe_type_affectation == '31' and line.pe_type_affectation in ['32', '33', '34', '35', '26', '37']:
                continue
            else:
                line.pe_type_affectation = pe_type_affectation

    @api.model
    def _get_pe_type_affectation(self):
        return self.env['pe.catalog.07'].get_selection()

    @api.onchange('product_id')
    def _onchange_product_id(self):
        # res = super(AccountMoveLine, self)._onchange_product_id()
        for line in self.filtered(lambda s: s.move_id.country_code=='PE'):
            pe_type_affectation = line._get_pe_type_affectation_by_tax()
            line.pe_type_affectation = pe_type_affectation
            if pe_type_affectation not in ['10','20','30','40']:
                line.discount = 100
            elif line.discount == 100:
                line.discount = 0
        return {}

    @api.model
    def get_pe_type_affectation_by_tax(self, taxes):
        tax_ids = taxes and taxes[0] or False
        res = False
        if tax_ids:
            if tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code in ['1000']):
                if tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code in ['9996']):
                    res = '11'
                else:
                    res = '10'
            elif tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code in ['9997']):
                if tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code in ['9996']):
                    res = '21'
                else:
                    res = '20'
            elif tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code in ['9998']):
                if tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code in ['9996']):
                    res = '31'
                else:
                    res = '30'
            elif tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code in ['9995']):
                res = '40'
        return res

    def _get_pe_type_affectation_by_tax(self, taxes = None):
        self.ensure_one()
        tax_ids = taxes or self.tax_ids
        res = False
        if tax_ids:
            if tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code in ['1000']):
                if tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code in ['9996']):
                    res = '11'
                else:
                    res = '10'
            elif tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code in ['9997']):
                if tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code in ['9996']):
                    res = '21'
                else:
                    res = '20'
            elif tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code in ['9998']):
                if tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code in ['9996']):
                    res = '31'
                else:
                    res = '30'
            elif tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code in ['9995']):
                res = '40'
        return res or '10'
 
    def _get_computed_taxes(self):
        res = super(AccountMoveLine, self)._get_computed_taxes()
        if self.pe_type_affectation and self.move_id.is_sale_document(include_receipts=True) and self.move_id.country_code=='PE':
            tax_is = self._set_free_tax(res.ids)
            res = self.env['account.tax'].browse(tax_is)
        return res
     
    def _set_free_tax(self, tax_ids):
        for line in self:
            res = tax_ids
            discount = 0
            if line.pe_type_affectation not in ['10', '20', '30', '40'] and line.move_id.is_sale_document(include_receipts=True):
                discount = 100
                free_tax= self.env['account.tax'].browse(tax_ids).filtered(lambda tax: tax.l10n_pe_edi_tax_code == '9996')
                if not free_tax:
                    free_tax= self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', '9996'),('type_tax_use','=','sale'),
                                                             ('company_id','=',line.move_id.company_id.id)], limit = 1)
                    res+=tax_ids + free_tax.ids
                else:
                    res = tax_ids
            elif line.move_id.is_sale_document(include_receipts=True):
                if  line.discount == 100:
                    discount = 0.0
                else:
                    discount = line.discount
                free_tax= self.env['account.tax'].browse(tax_ids).filtered(lambda tax: tax.l10n_pe_edi_tax_code == '9996')
                if free_tax:
                    free_tax= self.env['account.tax'].browse(tax_ids).filtered(lambda tax: tax.l10n_pe_edi_tax_code != '9996')
                    res = free_tax.ids
            line.discount = discount
            line.tax_ids = tax_ids
        return res
    
    @api.onchange('pe_type_affectation')
    def _onchange_pe_affectation_code(self):
        for line in self:
            if line.pe_type_affectation and line.move_id.is_sale_document(include_receipts=True):
                if line.pe_type_affectation in ['10', '11', '12', '13', '14', '15', '16', '17']:
                    ids = line.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code == '1000')
                    if not ids:
                        ids+= self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', '1000'),('type_tax_use','=','sale'),
                                                             ('company_id','=',line.move_id.company_id.id)], limit = 1)
                    
                    tax_ids = line._set_free_tax(ids.ids)                    
                elif line.pe_type_affectation in ['20', '21']:
                    ids = line.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code == '9997')
                    if not ids:
                        ids+= self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', '9997'),('type_tax_use','=','sale'),
                                                             ('company_id','=', line.move_id.company_id.id)], limit = 1)
                     
                    tax_ids = self._set_free_tax(ids.ids)
                elif self.pe_type_affectation in ['30', '31', '32', '33', '34', '35', '36']:
                    ids = self.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code == '9998').ids
                    res= self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', '9998'), ('id', 'in', ids)])
                    if not res:
                        res= self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', '9998'),('type_tax_use','=','sale'),
                                                             ('company_id','=',self.move_id.company_id.id)], limit = 1)
                     
                    tax_ids = self._set_free_tax(ids+res.ids)
                     
                elif self.pe_type_affectation in ['40']:
                    ids = self.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code == '9995').ids
                    res= self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', '9995'), ('id', 'in', ids)])
                    if not res:
                        res= self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', '9995'),('type_tax_use','=','sale'),
                                                             ('company_id','=',self.move_id.company_id.id)], limit = 1)
                     
                    tax_ids = self._set_free_tax(ids+res.ids)

    #Error de Odoo borrar cuando lo corrijan
    @api.depends('currency_id', 'company_id', 'move_id.date')
    def _compute_currency_rate(self):
        @lru_cache()
        def get_rate(from_currency, to_currency, company, date):
            return self.env['res.currency']._get_conversion_rate(
                from_currency=from_currency,
                to_currency=to_currency,
                company=company,
                date=date,
            )

        for line in self:
            if line.currency_id:
                line.currency_rate = get_rate(
                    from_currency=line.company_currency_id,
                    to_currency=line.currency_id,
                    company=line.company_id,
                    date=line.move_id.date or fields.Date.context_today(line),
                )
            else:
                line.currency_rate = 1