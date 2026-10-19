# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class GenerateLetters(models.TransientModel):
    _name = 'account.generate.letters'
    _description = 'Generate Letters'

    numero_letras = fields.Integer(string='Número de letras', required=True)
    default_test = fields.Char(string='Test', default='test')

    @api.model
    def _default_journal(self):
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        journal_id = self.env['account.journal'].search([('company_id','=',company_id),('type','=','bank'),('is_letter','=',True)], limit=1)
        if not journal_id:
            journal_id = self.env['account.journal'].search([('company_id','=',company_id),('type','=','bank'),('is_letter','=',True)], limit=1)
        return journal_id

    @api.model
    def _get_payment_type(self):
        if 'active_ids' in self._context:
            invoice_ids = self.env['account.move'].search([('id', 'in', self._context.get('active_ids'))])
            if invoice_ids.filtered(lambda x: x.move_type == 'in_invoice'):
                return 'outbound'
            elif invoice_ids.filtered(lambda x: x.move_type == 'out_invoice'):
                return 'inbound'
        else:
            return 'inbound'

    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], 
                             readonly=True, index=True, change_default=True, 
                             default=_get_payment_type)
    company_id = fields.Many2one('res.company', string='Company', required=True, 
                                 default=lambda self: self.env['res.company']._company_default_get('account.letter'))
    journal_id = fields.Many2one('account.journal', string='Journal', 
                                  default=_default_journal, domain="[('type', 'in', ['cash', 'bank', 'credit']),('is_letter','=',True),('company_id', '=', company_id)]")

    @api.onchange('numero_letras')
    def _compute_currency_id(self):
        active_ids = self._context.get('active_ids')
        invoice_ids = self.env['account.move'].search([('id', 'in', active_ids)])
        currency_ids = invoice_ids.mapped('currency_id')
        if len(currency_ids) > 1:
            raise ValidationError(_('No se pueden generar letras de pagos con diferentes monedas'))
        partner_ids = invoice_ids.mapped('partner_id')
        if len(partner_ids) > 1:
            raise ValidationError(_('No se pueden generar letras de pagos con diferentes proveedores'))
        self.proveedor_id = partner_ids[0]
        self.currency_id = currency_ids[0]
        self.total = sum(invoice_ids.mapped('amount_residual'))

    currency_id = fields.Many2one('res.currency', string='Moneda', compute= "_compute_currency_id")
    proveedor_id = fields.Many2one('res.partner', string='Proveedor', compute= "_compute_currency_id")

    total = fields.Float(string='Total', compute='_compute_currency_id')

    def generate_letters(self):
        number = 0
        amount_quote = round(self.total / self.numero_letras,2)
        total = 0
        letters_generated = self.env['account.letters.generated'].create({
            'name':'/',
            'proveedor_id':self.proveedor_id.id,
            'journal_id' : self.journal_id.id,
            'invoice_ids': [(6, 0, self._context.get('active_ids'))],
            'amount_total': self.total,
            'currency_id': self.currency_id.id,
            'partner_id': self.proveedor_id.id,
            'type':self.payment_type,
            })
        for i in range(0,self.numero_letras):
            number += 1
            if i == self.numero_letras - 1:
                amount_quote = self.total - total
            total += amount_quote
            self.env['account.letters.lines'].create({
                'generate_letter_id': letters_generated.id,
                'numero': number,
                'fecha': fields.Date.today(),
                'fecha_vencimiento':fields.Date.today(),
                'importe':amount_quote,
                'type':self.payment_type,
            })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.letters.generated',
            'view_mode': 'form',
            'context': {},
            'res_id': letters_generated.id,
            'target': 'new',
        }
    
    def generar_pagos(self):
        active_ids = self._context.get('active_ids')
        invoice_ids = self.env['account.move'].search([('id', 'in', active_ids)])
        currency_ids = invoice_ids.mapped('currency_id')
        if len(currency_ids) > 1:
            raise ValidationError(_('No se pueden generar letras de pagos con diferentes monedas'))
        partner_ids = invoice_ids.mapped('partner_id')
        if len(partner_ids) > 1:
            raise ValidationError(_('No se pueden generar letras de pagos con diferentes proveedores, revise su seleccion'))
        print('x')

class AccountLetterLines(models.TransientModel):
    _name = 'account.letters.generated'
    _description = 'Account Letters Lines'
    
    name = fields.Char(string='Letras')
    proveedor_id = fields.Many2one('res.partner', string='Proveedor',)
    line_ids = fields.One2many('account.letters.lines', 'generate_letter_id', string='Letters')
    total = fields.Float(string='Total')
    journal_id = fields.Many2one('account.journal', string='Journal', 
                                  domain="[('type', 'in', ['cash', 'bank', 'credit']),('is_letter','=',True),('company_id', '=', company_id)]")
    company_id = fields.Many2one('res.company', string='Company', 
                                 default=lambda self: self.env['res.company']._company_default_get('account.letter'))
    invoice_ids = fields.Many2many("account.move", "account_letter_generated_wizard_rel", 
                                   "letter_id", "invoice_id", "Invoices",
                                #    domain = "[('state','=', 'posted'),('partner_id','=',partner_id),('company_id','=',company_id)]"
                                   )
    type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], "Type", 
                             readonly=True, index=True, change_default=True)
    amount_total = fields.Float(string='Amount Total')
    currency_id = fields.Many2one("res.currency", "Currency")
    date = fields.Date(string='Fecha', default=fields.Date.today())
    partner_id = fields.Many2one("res.partner", "Partner")

    def confirmar_generacion(self):
        self.ensure_one()
        
        letter_ids = self.env['account.letter']
        partner_type = self.type == 'inbound' and 'customer' or 'supplier'
            
        invoice_now_ids = []   
        for line_id in self.line_ids:
            to_remove = []
            for invoice_id in line_id.generate_letter_id.invoice_ids:
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
                    'date_due': line_id.fecha_vencimiento,
                    'amount': line_id.importe,
                    'journal_id': self.journal_id.id,
                    'invoice_ids': [(6,0,invoice_now_ids)],
                    'partner_type': partner_type
                }
            letter_id = self.env['account.letter'].create(vals)
            letter_id.write({'amount':line_id.importe})
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


class AccountLetterLines(models.TransientModel):
    _name = 'account.letters.lines'
    _description = 'Account Letters Lines'

    numero = fields.Char(string='Numero')
    fecha = fields.Date(string='Fecha de creación')
    fecha_vencimiento = fields.Date(string='Fecha de vencimiento')
    importe = fields.Float(string='Importe')
    company_id = fields.Many2one('res.company', string='Company', related = "generate_letter_id.company_id", change_default=True, store=True, related_sudo=False)
    currency_id = fields.Many2one("res.currency", "Currency", related = "generate_letter_id.currency_id", change_default=True, store=True, related_sudo=False)
    type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], "Type",  related = "generate_letter_id.type", change_default=True, store=True, related_sudo=False)
    invoice_ids = fields.Many2many("account.move", "account_letters_lines_rel", 
                                   "letter_id", "invoice_id", "Invoices")
    generate_letter_id = fields.Many2one('account.letters.generated', string='Generate Letters')
