# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class AccountLetterReturned(models.TransientModel):
    _name = "account.letter.returned.wizard"
    _description = "Letter Returned"
    
    @api.model
    def _get_default_letter_id(self):
        return self.env.context.get('active_id')
    
    @api.model
    def _get_default_number(self):
        letter_id = self.env.context.get('active_id') and self.env['account.letter'].browse(self.env.context.get('active_id'))
        return letter_id and letter_id.number or False
    
    @api.model
    def _get_default_currency_id(self):
        active_id = self._get_default_letter_id()
        letter_id = self.env['account.letter'].browse(active_id)
        return letter_id.currency_id or self.env.company.currency_id
    
    name = fields.Char("Descripción", required=True)
    invoice_date = fields.Date(string='Fecha de Factura', required = True, default = fields.Date.context_today,
                               help="invoice date of the letter to our account")
    number = fields.Char("Número unico", required=True, default = _get_default_number)
    letter_id = fields.Many2one("account.letter", "Letter", default = _get_default_letter_id)
    currency_id = fields.Many2one('res.currency', string='Moneda', required=True, default=_get_default_currency_id)
    product_id = fields.Many2one('product.product', string='Producto')
    amount = fields.Monetary(string='Monto', required=True)
    amount_total = fields.Monetary(string='Amount Total', compute= '_compute_amount_total')
    
    
    @api.onchange('product_id')
    def product_id_change(self):
        if self.product_id:
            product = self.product_id.with_context(
                lang=self.letter_id.partner_id.lang,
                partner=self.letter_id.partner_id.id,
                quantity=1,
                date=self.letter_id.payment_date,
            )
            name = product.name_get()[0][1]
            self.name = name
            self.amount = product.list_price
    
    
    @api.depends('amount','product_id','currency_id')
    def _compute_amount_total(self):
        self.ensure_one()
        amount_total=0
        if self.product_id.taxes_id:
            taxes = self.product_id.taxes_id.compute_all(self.amount, self.currency_id, 1, product=self.product_id, partner=self.letter_id.partner_id)
            amount_total = taxes['total_excluded']
        else:
            amount_total = self.amount
        self.amount_total = amount_total
    
    
    def action_returned(self):
        self.ensure_one()
        if not self.letter_id:
            raise ValidationError(_("It is necessary that it is associated with a letter"))
        invoice_id = self.letter_id.create_invoice_from_letter(self.product_id, self.amount, self.name)
        invoice_id._onchange_partner_id()
        invoice_id.invoice_line_ids._set_taxes()
        payment_ids = self.letter_id.cancel()
        self.letter_id.write({'state': 'returned'})
        return self.letter_id.button_debit_invoices()    


    
    