# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    pe_qty_fees = fields.Integer("Fees", default = 1)
    pe_payment_lines = fields.One2many('pe.payment.date', 'order_id', 'Payment Lines')
    
    def generate_pe_fees(self):
        self.ensure_one()
        if self.pe_qty_fees<=0:
            raise ValidationError(_("The quotas must be greater than zero?"))
        elif not self.payment_term_id:
            raise ValidationError(_("Payment termn is required"))
        elif self.amount_total <= 0.0:
            raise ValidationError(_("The total must be greater than zero "))
        
        pe_payment_date_start = fields.Date.context_today(self)
        
        pe_payment_date_end = self.payment_term_id._get_last_discount_date(pe_payment_date_start)

        self.pe_payment_lines.unlink()
        vals = dict(self.env.context)
        # product_ids = self.order_line.mapped('product_id').filtered(lambda s:s.pe_detraction)
        # dtr = 0.0
        # for product_id in product_ids:
        #     if int(product_id.pe_detraction)>=dtr and self.amount_total>=700:
        #         dtr = int(product_id.pe_detraction)
                
        vals['pe_payment_date_start'] = pe_payment_date_start
        vals['pe_payment_date_end'] = fields.Date.from_string(pe_payment_date_end)
        vals['pe_payment_qty'] = self.pe_qty_fees
        vals['pe_payment_amount'] = self.amount_total #*(1-dtr/100)
        pe_payment_lines = self.env['pe.payment.date'].get_payment_by_qty_date(vals)
        self.pe_payment_lines = pe_payment_lines
    
    def _get_pe_default_journal(self, pe_invoice_code):
        self.ensure_one()
        journal_id = False
        if pe_invoice_code:
            # journal = self.env['account.journal'].browse(invoice_vals.get('journal_id'))
            type = 'sale'
            journal_id = False
            if type == 'sale':
                journal_id = self.env.user.pe_journal_ids.filtered(lambda s: s.pe_invoice_code == pe_invoice_code and s.type == type and s.company_id == self.company_id)
            if not journal_id:
                journal_id = self.env['account.journal'].search([('pe_invoice_code','=',pe_invoice_code),
                                                                 ('type','=',type),
                                                                 ('company_id','=',self.company_id.id)], limit = 1)
            journal_id = journal_id.id
        return journal_id or False
    
    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        if self.partner_id.pe_doc_type == '6':
            pe_invoice_code = '01'
        else:
            pe_invoice_code = '03'
        if pe_invoice_code and self._get_pe_default_journal(pe_invoice_code):
            res['journal_id'] = self._get_pe_default_journal(pe_invoice_code)
        res['pe_qty_fees'] = self.pe_qty_fees
        if self.pe_payment_lines:
            res['pe_payment_lines'] = self.pe_payment_lines.get_payment_values()
        return res

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    def _get_pe_type_affectation_by_tax(self, taxes = None):
        self.ensure_one()
        tax_ids = taxes or self.tax_id
        res = False
        if tax_ids:
            if tax_ids.filtered(lambda tax: tax.pe_tax_type.code in ['1000']):
                if self.discount == 100:
                    res = '11'
                else:
                    res = '10'
            elif tax_ids.filtered(lambda tax: tax.pe_tax_type.code in ['9997']):
                if self.discount == 100:
                    res = '21'
                else:
                    res = '20'
            elif tax_ids.filtered(lambda tax: tax.pe_tax_type.code in ['9998']):
                if self.discount == 100:
                    res = '31'
                else:
                    res = '30'
            elif tax_ids.filtered(lambda tax: tax.pe_tax_type.code in ['9995']):
                res = '40'
        return res

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        res['pe_type_affectation'] = self._get_pe_type_affectation_by_tax()
        if self.discount == 100 and not self.tax_id.filtered(lambda tax: tax.pe_tax_type.code in ['9998']):
            tax_id = self.env['account.tax'].search(
                [('l10n_pe_edi_tax_code', '=', '9996'), ('type_tax_use', '=', 'sale')], limit=1)
            tax_ids = [(6, 0, self.tax_id.ids + tax_id.ids)]
            res['tax_ids'] = tax_ids
        return res