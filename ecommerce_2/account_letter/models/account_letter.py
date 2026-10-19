# -*- coding: utf-8 -*-

from odoo import models, fields, api, _ 
from odoo.tools import float_compare, float_is_zero
from odoo.exceptions import ValidationError, UserError
from num2words import num2words
from datetime import datetime

class AccountLetter(models.Model):
    _name = 'account.letter'
    _description = 'Accounting Letters'
    _inherit = ['mail.thread','mail.activity.mixin', 'portal.mixin']

    name = fields.Char(string="Numero", readonly=True)
    invoice_type = fields.Selection(string="Tipo de factura", selection=[('out_invoice','Customer Bills'),('in_invoice','Verdors Bill')])
    number = fields.Char("Número unico", copy= False)
    invoice_ids = fields.Many2many('account.move', 'account_invoice_letter_rel', 'payment_id', 'invoice_id', string="Facturas", copy=False, 
                                   help="""Technical field containing the invoice for which the payment has been generated.
                                   This does not especially correspond to the invoices reconciled with the payment,
                                   as it can have been generated first, and reconciled later""", domain="[('move_type','=',invoice_type),('payment_state','=','not_paid')]")
    state = fields.Selection(string="Estado",selection=[
            ('draft', 'Borrador'),
            ('posted', 'Confirmado'),
            ('accepted', 'Aceptada'),
            ('accepted_bank', 'Aceptada por Banco'),
            ('declined', 'Declinada'),
            ('renewed', 'Renewed'),
            ('paid', 'Pagada'),
            ('withdrawal_request', 'Retiro a solicitud'),
            ('returned', 'Devuelto'),
            ('cancelled','Cancelado')
            ],
            ondelete={
            'draft':'cascade',
            'posted':'cascade',
            'accepted': 'cascade',
            'accepted_bank': 'cascade',
            'declined': 'cascade',
            'renewed': 'cascade',
            'paid': 'cascade',
            'withdrawal_request': 'cascade',
            'returned': 'cascade',
            'cancelled': 'cascade'
        },default='draft')
    date_due = fields.Date(string='Fecha de vencimiento', required=True, copy=False)
    date = fields.Date(string='Fecha', required=True, copy=False)
    partner_id = fields.Many2one(string="Tercero",comodel_name='res.partner', required=True)

    partner_type = fields.Selection([
        ('customer', 'Cliente'),
        ('supplier', 'Proveedor'),
    ], default='customer', store=True)

    payment_type = fields.Selection([
        ('outbound', 'Enviar'),
        ('inbound', 'Recibir'),
    ], string='Payment Type', store=True)

    
    journal_id = fields.Many2one('account.journal', string='Diario de pago', required=True, domain=lambda self: [('type', 'in', ['cash', 'bank', 'credit']),('is_letter','=',True),('company_id','=',self.env.company.id)])

    payment_ids = fields.One2many('account.letter.payment', 'letter_id', string='Pagos', readonly=True)

    # move_line_ids = fields.One2many('account.move.line', 'letter_id', readonly=True, copy=False)
    
    transfer_move_name = fields.Char(string='Nombre de entrada', readonly=True,
        default=False, copy=False,
        help="Technical field holding the number given to the journal entry, automatically set when the statement line is reconciled then stored to set the same number again if the line is cancelled, set to draft and re-processed again.")
    company_id = fields.Many2one('res.company', string='Compañia', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Moneda', required=True, default=lambda self: self.env.company.currency_id)
    amount_residual = fields.Monetary(string='Monto pendiente', 
        compute='_amount_residual', 
        help="The residual amount on a journal item expressed in the company currency.")

    def _inverse_amount(self):
        pass
    amount = fields.Monetary(string='Monto', 
        compute='_compute_amount', store=True,inverse="_inverse_amount",
        help="The sum of amounts of invoices.", readonly=True)
    
    refund_id = fields.Many2one("account.move", "Factura de reembolso")
    user_id = fields.Many2one('res.users', string='Vendedor', tracking=True,
        readonly=True,
        default=lambda self: self.env.user, copy=False)
    
    active = fields.Boolean(string='Activo', default=True)
    
    is_sent = fields.Boolean(string="Enviado", default=False)

    payment_id = fields.Many2one(string='Pago',comodel_name='account.payment')

    letter_ids = fields.Many2many(string="Letras asociadas",comodel_name='account.letter',
        relation='account_letter_account_letter_rel',
        column1='rel_letter_id',
        column2='letter_id', )

    has_letter_ids = fields.Boolean(string="Tiene muchas letras?",compute="_compute_has_letter")

    def _compute_has_letter(self):
        for r in self:
            if r.letter_ids:
                r.has_letter_ids = True
            else:
                r.has_letter_ids = False

    def toggle_sent(self):
        if self.is_sent:
            self.is_sent= False
        else:
            self.is_sent= True

    def letter_pdf_print(self):
        self.ensure_one()
        self.is_sent = True
        return self.env.ref('account_letter.account_letter_pdf').report_action(self)

    @api.depends('invoice_ids')
    def _compute_amount(self):
        for r in self:
            r.amount = sum(r.invoice_ids.mapped("amount_total"))
            

    def action_unarchive(self):
        for r in self:
            r.write({'active': True})
    
    
    def action_archive(self):
        for r in self:
            r.write({'active': False})

    
    @api.depends('payment_ids')
    def _amount_residual(self):
        for letter in self:
            amount_invoice = letter.amount
            amount_payment = sum(letter.payment_ids.mapped('amount'))

            letter.amount_residual = amount_invoice - amount_payment
            if letter.amount_residual == 0:
                if not letter.payment_ids.filtered(lambda x: x.from_bank):
                    letter.state = 'paid'
            # if letter.amount_residual == 0 and letter.state != 'accepted_bank':
            #     letter.state = 'paid'


    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        res = {}
        domain = res.get('domain', {})
        invoice = [('state','=','posted'),('company_id','=',self.env.company.id)]
        if self.payment_type == 'inbound':
            invoice.append(('type','=','out_invoice'))
        else:
            invoice.append(('type','=','in_invoice'))
        if self.partner_id:
            invoice.append(('partner_id','=',self.partner_id.id))
        domain.update({'invoice_ids':invoice})
        res['domain'] = domain
        return res
    
    
    def action_accepted_bank(self):
        self.ensure_one()
        # transfer_paramns = {'letter_id':self.id,
        #                     'amount': self.amount_residual,
        #                     'payment_date':datetime.today().date(),
        #                     'currency_id': self.currency_id.id,
        #                     'from_bank':True
        #                     }
        # payment_id = self.env['account.letter.payment'].create(transfer_paramns)
        # payment_id.validate()
        self.state = 'accepted_bank'

    
    def action_register_payment(self):
        self.ensure_one()
        if not self:
            return ''
        context = dict(self.env.context)
        context['active_id'] = self.id
        amount = self.amount_residual
        context['default_amount'] = amount
        return {
            'name': _('Register Payment'),
            'res_model': 'account.letter.payment.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('account_letter.account_letter_payment_wizard_view').id,
            'context': context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
    
    
    def action_declined(self):
        self.write({'state': 'declined'})
    
    
    def action_withdrawal_request(self):
        self.write({'state': 'withdrawal_request'})
    
    
    def action_returned(self):
        self.ensure_one()
        if not self:
            return ''
        context = dict(self.env.context)
        context['active_id'] = self.id
        amount = self.amount_residual
        context['default_amount'] = amount
        return {
            'name': _('Returned'),
            'res_model': 'account.letter.returned.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('account_letter.view_account_letter_returned_wizard').id,
            'context': context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def _generate_multiple_payment(self):
        payment_values = {}
        amount_total = sum(self.mapped('amount_residual'))

        payment_values = {
            'payment_type':self[0].payment_type,
            'partner_id': self[0].partner_id.id,
            'partner_type':self[0].partner_type,
            'amount':amount_total,
            'date':self[0].date,
            'journal_id':self[0].journal_id.id,
        }
        payment_id = self.env['account.payment'].create([payment_values])
        if not payment_id:
            raise UserError("No fue posible crear el pago para la factura")
        # payment_id.write({'payment_type':self[0].payment_type})
        payment_id.action_post()
        if self[0].payment_type == 'outbound':
            line = payment_id.move_id.line_ids.filtered(lambda line: line.debit > 0)
            for move_id in self.mapped('invoice_ids'):
                move_id.js_assign_outstanding_line(line.id)
            for r in self:
                if not r.name:
                    r.name = self.env['ir.sequence'].with_company(r.company_id).next_by_code(
                                'account.letter.sequence.out',
                                sequence_date=r.date,
                            )
        else:
            line = payment_id.move_id.line_ids.filtered(lambda line: line.credit > 0)
            for move_id in self.mapped('invoice_ids'):
                move_id.js_assign_outstanding_line(line.id)
            for r in self:
                if not r.name:
                    r.name = self.env['ir.sequence'].with_company(self.company_id).next_by_code(
                            'account.letter.sequence.in',
                            sequence_date=self.date,
                        )
        for r in self:
            r.payment_id = payment_id.id

    def _generate_payment(self):
        if not self.payment_id:
            payment_values = {
                'payment_type':self.payment_type,
                'partner_id': self.partner_id.id,
                'amount':self.amount,
                'date':self.date,
                'journal_id':self.journal_id.id,
            }
            payment_id = self.env['account.payment'].create([payment_values])
            payment_id.action_post()
            if self.payment_type == 'outbound':
                line = payment_id.move_id.line_ids.filtered(lambda line: line.debit > 0)
                for move_id in self.invoice_ids:
                    move_id.js_assign_outstanding_line(line.id)
                if not self.name:
                    self.name = self.env['ir.sequence'].with_company(self.company_id).next_by_code(
                                'account.letter.sequence.out',
                                sequence_date=self.date,
                            )
            else:
                line = payment_id.move_id.line_ids.filtered(lambda line: line.credit > 0)
                for move_id in self.invoice_ids:
                    move_id.js_assign_outstanding_line(line.id)
                if not self.name:
                    self.name = self.env['ir.sequence'].with_company(self.company_id).next_by_code(
                                'account.letter.sequence.in',
                                sequence_date=self.date,
                            )
            self.payment_id = payment_id.id

    def unlink(self):
        for r in self:
            if r.state not in ['cancelled','draft']:
                raise UserError("Para poder eliminar una letra debe estar en estado cancelado o borrador, recuerda que si la letra a eliminar tiene multiples letras estas tambien se eliminaran!")
        ids = self
        ids |= self.mapped('letter_ids')
        return super(AccountLetter, ids).unlink()

    def action_post(self):
        #TODO: registrar el pago creando un account.payment y asociandolos a las facturas
        if self.env.context.get('multiple_letter',False):
            self._generate_multiple_payment()
        elif self.letter_ids:
            self.letter_ids._generate_multiple_payment()
        else:
            self._generate_payment()
        if self.letter_ids:
            self.letter_ids.state = 'posted'
        else:
            self.state = 'posted'
        return True
    
    def action_cancel(self):
        if self.letter_ids:
            self.letter_ids.mapped('payment_id').sudo().action_draft()
            self.letter_ids.mapped('payment_id').sudo().action_cancel()
            self.letter_ids.mapped('payment_id').sudo().unlink()
            for letter in self.letter_ids:
                letter.payment_ids.unlink()
                letter.state = 'cancelled'
        else:
            self.mapped('payment_id').sudo().action_draft()
            self.mapped('payment_id').sudo().action_cancel()
            self.mapped('payment_id').sudo().unlink()
            self.state = 'cancelled'
        return True

    def action_cance_multiple(self):
        names = self.letter_ids.mapped('name')
        message = "Esta letra fue generada con letras multiples, al cancelarla se cancelaran las siguientes letras {letras}".format(letras=str(names))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirmar Cancelar',
            'res_model': 'cancel.letter.confirm.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.id,
                'default_message':message
            }
        }
    def action_draft(self):
        #TODO: pasar a borrador
        if self.letter_ids:
            # self.letter_ids.mapped('payment_id').sudo().action_draft()
            # self.letter_ids.mapped('payment_id').sudo().action_cancel()
            # self.letter_ids.mapped('payment_id').sudo().unlink()
            for letter in self.letter_ids:
                letter.state = 'draft'
        else:
            # self.mapped('payment_id').sudo().action_draft()
            # self.mapped('payment_id').sudo().action_cancel()
            # self.mapped('payment_id').sudo().unlink()
            self.state = 'draft'
        return True

    def get_amount_in_letter(self):
        self.ensure_one()
        amount = int(self.amount)
        cents = int((self.amount - amount)*100)
        res = num2words(amount, lang='es').upper() + " Y %s/100 %s" %(str(cents), (self.currency_id.currency_unit_label or self.currency_id.name).upper()) 
        return res
    
    
    

    
    def action_letter_sent(self):
        self.ensure_one()
        template = self.env.ref('account_letter.email_template_edi_letter', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='account.letter',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            force_email=True
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    @api.onchange('state')
    def _onchange_state(self):
        for r in self:
            if r.state == 'posted':
                r._onchange_payment_ids()
                

    

class account_payment_payment(models.Model):
    _name = "account.letter.payment"
    _description = "Default Description"

    letter_id = fields.Many2one("account.letter", "Letter")
    company_id = fields.Many2one('res.company', related='letter_id.company_id', string='Company', readonly=True)
    transfer_move_name = fields.Char(string='Transfer Entry Name', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id)
    amount = fields.Monetary(string='Amount', required=True)
    journal_id = fields.Many2one('account.journal', string='Journal', )
    payment_date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    state = fields.Selection(selection=[
                            ('draft', 'Draft'),
                            ('posted', 'Posted'),
                            ('cancel', 'Cancelled')
                        ], string='Status')

    from_bank = fields.Boolean(string="Aceptado desde banco")
    payment_id = fields.Many2one(string="Pago",comodel_name='account.payment')
    def validate(self):
        for line in self:
            line.letter_id._amount_residual()
        return True

