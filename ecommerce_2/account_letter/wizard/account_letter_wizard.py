# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import float_compare, float_is_zero
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from odoo.addons import decimal_precision as dp

class AccountLetterInvoiceWizard(models.TransientModel):
    _name = 'account.letter.invoice.wizard'
    _description = 'Default Description'
    
    
    @api.model
    def _default_journal(self):
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        journal_id = self.env['account.journal'].search([('company_id','=',company_id),('type','=','bank'),('is_letter','=',True)], limit=1)
        if not journal_id:
            journal_id = self.env['account.journal'].search([('company_id','=',company_id),('type','=','bank'),('is_letter','=',True)], limit=1)
        return journal_id

    partner_id = fields.Many2one("res.partner", "Partner", required = True)
    amount_invoice = fields.Monetary("Total Invoice", compute = "compute_amount")
    amount = fields.Monetary("Amount", required = False)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id)
    invoice_type = fields.Selection(string="Invoice Type", selection=[('out_invoice','Customer Bills'),('in_invoice','Verdors Bill')])
    invoice_ids = fields.Many2many("account.move", "account_letter_invoice_wizard_rel", 
                                   "letter_id", "invoice_id", "Invoices",
                                    domain="[('currency_id', '=', currency_id),('move_type','=',invoice_type),('payment_state','=','not_paid')]"
                                   )
    
    date = fields.Date("Date", required=True, default = fields.Date.context_today)
    
    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], 
                             readonly=True, index=True, change_default=True, 
                             default=lambda self: self._context.get('default_payment_type', 'inbound'))
    quantity_fees = fields.Integer("Quantity of fees", default = 1, required = True)
    days_period = fields.Integer("Days period", required = True, default = 15)
    days_first_period = fields.Integer("Days First period", required = True, default = 15)
    start_date = fields.Date("Start Date")
    due_date = fields.Date("First Due Date", compute = "compute_due_date", inverse = "inverse_due_date")
    journal_id = fields.Many2one('account.journal', string='Payment Journal', required=True, domain=lambda self: [('type', 'in', ['cash', 'bank', 'credit']),('is_letter','=',True),('company_id','=',self.env.company.id)])
        
    @api.depends('days_period', 'start_date', 'date')
    def compute_due_date(self):
        for line in self:
            due_date = fields.Date.from_string(line.start_date or line.date) + timedelta(line.days_first_period)
            line.due_date = fields.Date.to_string(due_date)
    
    
    def inverse_due_date(self):
        for line in self:
            start_date = fields.Date.from_string(line.due_date) - timedelta(line.days_first_period)
            line.start_date = fields.Date.to_string(start_date)
            
    @api.onchange('days_first_period')
    def onchange_days_period(self):
        self.due_date = fields.Date.from_string(self.start_date or self.date) + timedelta(self.days_first_period)
        self.days_period = self.days_first_period
    
    
    
    @api.depends("currency_id", "invoice_ids")
    def compute_amount(self):
        self.ensure_one()
        amount = 0.0
        if self.invoice_ids:
            for invoice_id in self.invoice_ids:
                amount += invoice_id.amount_residual
        self.amount_invoice = amount
    
    
    def get_periods(self):
        self.ensure_one()
        vals = {}
        if self.due_date and self.days_first_period:
            date = fields.Date.to_string(fields.Date.from_string(self.due_date) - timedelta(self.days_first_period))
        else:
            date = self.start_date or self.date
        for i in range(self.quantity_fees):
            dt = fields.Date.from_string(date)
            if i == 0:
                date = fields.Date.to_string((dt+timedelta(self.days_first_period)))
            else:
                date = fields.Date.to_string((dt+timedelta(self.days_period)))
            vals[i] = date
        return vals
    
    
    def get_letter_lines(self):
        self.ensure_one()
        invoice_ids = self.env['account.move'].search([('id','in', self.invoice_ids.ids)], order = "invoice_date ASC, name ASC").ids
        fees_amount = round(self.amount / self.quantity_fees)
        dates = self.get_periods()
        lines = []
        amount = self.amount 
        for i in range(self.quantity_fees):
            vals = {}
            credit = fees_amount
            vals['date_due'] = dates[i]
            if  i+1==self.quantity_fees:
                vals['amount'] = amount
            else:
                vals['amount'] = fees_amount
            amount-= fees_amount
            vals['partner_id'] = self.partner_id.id
            lines.append((0,0,vals))
        return lines
                    
    
    
    def action_confirm(self):
        self.ensure_one()
        if self.amount == 0.0:
            self.amount =  self.amount_invoice
        if self.amount == 0.0:
            raise ValidationError(_("The total cannot be zero"))
        
        invoice_total = 0.0
        frist_invoice = True
        for invoice_id in self.invoice_ids:
            if frist_invoice:
                frist_invoice = False
                continue
            invoice_total += invoice_id.amount_residual
        if self.amount < invoice_total:
            raise ValidationError(_("The residual of the invoices exceeds the amount of the letter"))
        
        vals = {
                'company_id': self.company_id.id,
                'currency_id': self.currency_id.id,
                'partner_id': self.partner_id.id,
                'date': self.date,
                'type': self.payment_type,
                'journal_id': self.journal_id.id,
            }
        vals['line_ids'] = self.get_letter_lines()
        vals['invoice_ids'] = [(6, 0, self.invoice_ids.ids)]
        letters_id = self.env['account.letter.wizard'].create(vals)
        #letters_id.invoice_ids = [(6, 0, self.invoice_ids.ids)]
        form_res = self.env.ref('account_letter.account_letters_wizard_wizard')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.letter.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {},
            'res_id': letters_id.id,
            'views': [(form_res.id, 'form')],
            'target': 'new',
        }

class AccountLetterWizard(models.TransientModel):
    _name = 'account.letter.wizard'
    _description = 'Default Description'

    currency_id = fields.Many2one("res.currency", "Currency", required = True, readonly = True)
    amount_total = fields.Monetary("Total", compute = "_compute_total", readonly = True)
    company_id = fields.Many2one('res.company', string='Company', required=True, 
                                 default=lambda self: self.env['res.company']._company_default_get('account.letter'), readonly = True)
    date = fields.Date("Date", required=True, readonly = True)
    partner_id = fields.Many2one("res.partner", "Partner", required = True)
    type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], "Type", 
                             readonly=True, index=True, change_default=True)
    line_ids = fields.One2many("account.letter.line.wizard", "letters_id", "Letter")
    journal_id = fields.Many2one('account.journal', string='Journal', 
                                 required=True, domain="[('type', 'in', ['bank']), ('company_id', '=', company_id)]")
    invoice_ids = fields.Many2many("account.move", "account_letter_inv_wizard_rel", 
                                   "letter_id", "invoice_id", "Invoices",
                                   domain = "[('state','=', 'posted'),('partner_id','=',partner_id),('company_id','=',company_id)]")
    amount_total_lines = fields.Monetary(
        "Total 2", compute="_compute_total_lines")

    show_msg = fields.Boolean('Msg', compute="_compute_show_msg")

    @api.depends('line_ids')
    def _compute_total_lines(self):
        for letter in self:
            amount_total = 0.0
            for line in letter.line_ids:
                amount_total += line.amount_total
            letter.amount_total_lines = amount_total

    @api.depends('amount_total_lines', 'amount_total')
    def _compute_show_msg(self):
        for letter in self:
            letter.show_msg = False
            if letter.amount_total_lines != letter.amount_total:
                letter.show_msg = True


    @api.depends('invoice_ids')
    def _compute_total(self):
        for letter in self:
            amount_total = 0.0
            for line in letter.line_ids:
                amount_total+=line.amount_total
            letter.amount_total = amount_total
    
    
    
    def action_confirm(self):
        self.ensure_one()
        
        letter_ids = self.env['account.letter']
        partner_type = self.type == 'inbound' and 'customer' or 'supplier'
            
        invoice_now_ids = []   
        for line_id in self.line_ids:
            to_remove = []
            for invoice_id in self.invoice_ids:
                if invoice_id.id not in invoice_now_ids:
                    invoice_now_ids.append(invoice_id.id)
                if invoice_now_ids:
                    for invoice_id1 in invoice_now_ids:
                        if self.env['account.move'].browse(invoice_id1).payment_state == 'paid':
                            if invoice_id1 not in to_remove:
                                to_remove.append(invoice_id1)
            for invoice_id_to_remove in to_remove:
                invoice_now_ids.remove(invoice_id_to_remove)
                
            vals = {
                    'company_id': line_id.company_id.id,
                    'currency_id': line_id.currency_id.id,
                    'partner_id': self.partner_id.id,
                    'date': self.date,
                    'payment_type': self.type,
                    'date_due': line_id.date_due,
                    'amount': line_id.amount,
                    'journal_id': self.journal_id.id,
                    'invoice_ids': [(6,0,invoice_now_ids)],
                    'partner_type': partner_type
                }
            letter_id = self.env['account.letter'].create(vals)
            letter_id.write({'amount':line_id.amount})
            letter_ids += letter_id
        letter_ids.with_context({'multiple_letter':True}).action_post()
        for letter_id in letter_ids:
            letter_id.write({
                'letter_ids':[(6,0,letter_ids.ids)]
            })
        action = {
            'name': _('Letters'),
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'account.letter',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', letter_ids.ids)],
        }
        if self.type == 'outbound':
            action['views'] = [(self.env.ref('account_letter.view_account_letter_list').id, 'list'), (self.env.ref('account_letter.view_account_letter_form').id, 'form')]
            action['context'] = {'default_payment_type': 'outbound','default_invoice_type':'out_invoice'}
        else:
            action['context'] = {'default_payment_type': 'inbound','default_invoice_type':'in_invoice'}
            action['views'] = [(self.env.ref('account_letter.view_account_letter_list').id, 'list'), (self.env.ref('account_letter.view_account_letter_form').id, 'form')]
        return action
        

class AccountLetterLineWizard(models.TransientModel):
    _name = 'account.letter.line.wizard'
    _description = 'Default Description'

    amount = fields.Monetary("Amount")
    date = fields.Date("Start Date", related="letters_id.date")
    date_due = fields.Date(string='Due Date', required=True)
    letters_id = fields.Many2one("account.letter.wizard", "Letter")
    company_id = fields.Many2one('res.company', string='Company', related = "letters_id.company_id", change_default=True, store=True, related_sudo=False)
    partner_id = fields.Many2one("res.partner", "Partner", related = "letters_id.partner_id", change_default=True, store=True, related_sudo=False)
    currency_id = fields.Many2one("res.currency", "Currency", related = "letters_id.currency_id", change_default=True, store=True, related_sudo=False)
    line_ids = fields.One2many("account.letter.line.invoice.wizard", "inv_letter_id", "Letter Lines")
    amount_total = fields.Monetary("Total", compute = "_compute_amount_total", inverse = "_inverse_amount_total")
    type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], "Type",  related = "letters_id.type", change_default=True, store=True, related_sudo=False)
    invoice_ids = fields.Many2many("account.move", "account_letter_line_wizard_rel", 
                                   "letter_id", "invoice_id", "Invoices")
    
    
    
    @api.depends("line_ids.invoice_id", "line_ids.amount")
    def _compute_amount_total(self):
        for line in self:
            if not line.line_ids:
                line.amount_total = line.amount
            else:
                amount = 0.0
                for inv_line in line.line_ids:
                    amount+=inv_line.amount
                line.amount_total = amount
    
    
    @api.depends("line_ids.invoice_id", "line_ids.amount")
    def _inverse_amount_total(self):
        for line in self:
            if not line.line_ids:
                line.amount = line.amount_total
            else:
                amount = line.amount_total
                amount_line = amount/len(line.line_ids)
                for inv_line in line.line_ids:
                    inv_line.amount = amount_line
    
    def button_edit_invoices(self):
        self.ensure_one()
        view = self.env.ref(
            'account_letters.view_account_letters_line_wizard'
        )
        return {
            'name': _('Invoices'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.letters.line.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': self.env.context,
        }

class AccountLetterLineInvoiceWizard(models.TransientModel):
    _name = 'account.letter.line.invoice.wizard'
    _description = 'Default Description'

    invoice_id = fields.Many2one('account.move', string='Invoice Reference', required=True)
    invoice_residual = fields.Monetary(string='Amount Due', related = "invoice_id.amount_residual")
    amount = fields.Monetary(string='Amount', required=True)
    inv_letter_id = fields.Many2one('account.letter.line.wizard', string='Letter')
    company_id = fields.Many2one('res.company', string='Company', related = "inv_letter_id.company_id", change_default=True, store=True, related_sudo=False)
    currency_id = fields.Many2one('res.currency', related='inv_letter_id.currency_id', store=True, related_sudo=False)
    
    @api.onchange('invoice_id')
    def onchange_invoice_id(self):
        if self.invoice_id and self.inv_letter_id:
            currency_id = self.invoice_id.currency_id.with_context(date=self.inv_letter_id.date)
            amount = currency_id.compute(self.invoice_id.residual, self.currency_id)
            self.amount = amount
        


    
class ConfirmWizard(models.TransientModel):
    _name = 'cancel.letter.confirm.wizard'
    _description = 'Confirmación Cancelar'

    message = fields.Text(string="Mensaje",readonly=True)
    letter_id = fields.Many2one(string="Letra",comodel_name="account.letter",default=lambda self: self.env.context.get('active_id'))
    

    def action_confirm(self):
        # Ejecutar acción en el modelo principal
        self.letter_id.action_cancel()
        return {'type': 'ir.actions.act_window_close'}
