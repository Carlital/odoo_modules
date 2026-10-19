# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero

class AccountLetterPayment(models.TransientModel):
    _name = "account.letter.payment.wizard"
    _description = "Letter Payment Wizard"
    
    @api.model
    def _get_default_letter_id(self):
        return self.env.context.get('active_id')
    
    @api.model
    def _get_default_communication(self):
        active_id = self._get_default_letter_id()
        letter_id = self.env['account.letter'].browse(active_id)
        return letter_id.name or False
    @api.model
    def _get_default_currency_id(self):
        active_id = self._get_default_letter_id()
        letter_id = self.env['account.letter'].browse(active_id)
        return letter_id.currency_id or self.env.company.currency_id
    
    letter_id = fields.Many2one("account.letter", "Letra", default = _get_default_letter_id)
    journal_id = fields.Many2one('account.journal', string='Diario de pago', required=True, domain="[('type', 'in', ('bank', 'cash'))]")
    company_id = fields.Many2one('res.company', related='letter_id.company_id', string='Compañia', readonly=True)
    amount = fields.Monetary(string='Monto', required=True)
    currency_id = fields.Many2one('res.currency', string='Moneda', required=True, default=_get_default_currency_id, readonly=True)
    payment_date = fields.Date(string='Fecha', default=fields.Date.context_today, required=True)
    communication = fields.Char(string='Memo', default = _get_default_communication)
    
    
    def validate(self):
        self.ensure_one()
        if self.amount == 0:
            raise ValidationError(_('El monto de pago no puede ser negativo.'))
        if self.letter_id.amount < self.amount:
            raise ValidationError(_('El monto de pago no puede exceder al de la letra.'))

        transfer_paramns = {    'letter_id':self.letter_id.id,
                                'amount': self.amount,
                                'payment_date':self.payment_date,
                                'journal_id':self.journal_id.id,
                                'currency_id': self.currency_id.id,
                                }
        payment_id = self.env['account.letter.payment'].create(transfer_paramns)
        payment_id.validate()

        payment_values = {
            # 'payment_type':self.letter_id.payment_type,
            'partner_id': self.letter_id.partner_id.id,
            'partner_type':self.letter_id.partner_type,
            'amount':self.amount,
            'date':self.payment_date,
            'journal_id':self.journal_id.id,
            'memo':self.communication
        }
        payment_account_id = self.env['account.payment'].create([payment_values])
        payment_account_id.action_post()
        payment_id.payment_id = payment_account_id
    
    
    