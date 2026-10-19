from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class SaleOrderPaymentWizard(models.TransientModel):
    _name = 'sale.order.payment.wizard'
    _description = 'Configuración de Pagos de Pedido de Venta'

    sale_order_id = fields.Many2one('sale.order', string='Pedido de Venta', required=True)
    amount_total = fields.Monetary(string='Total del Pedido', related='sale_order_id.amount_total', readonly=True)
    payment_line_ids = fields.One2many('sale.order.payment.wizard.line', 'wizard_id', string='Líneas de Pago')
    amount_paid = fields.Monetary(string='Total Pagado', compute='_compute_amount_paid', store=False)
    amount_due = fields.Monetary(string='Saldo Pendiente', compute='_compute_amount_due', store=False)
    currency_id = fields.Many2one('res.currency', related='sale_order_id.currency_id')

    @api.depends('payment_line_ids', 'payment_line_ids.amount')
    def _compute_amount_paid(self):
        for wizard in self:
            wizard.amount_paid = sum(line.amount for line in wizard.payment_line_ids)

    @api.depends('amount_total', 'amount_paid')
    def _compute_amount_due(self):
        for wizard in self:
            wizard.amount_due = wizard.amount_total - wizard.amount_paid

    @api.onchange('payment_line_ids')
    def _onchange_payment_line_ids(self):
        """Recalcular amount_paid y amount_due cuando cambian las líneas de pago"""
        self._compute_amount_paid()
        self._compute_amount_due()
        # Forzar la actualización de la vista
        return {
            'value': {
                'amount_paid': self.amount_paid,
                'amount_due': self.amount_due
            }
        }

    @api.model
    def default_get(self, fields):
        res = super(SaleOrderPaymentWizard, self).default_get(fields)
        if 'sale_order_id' in res:
            sale_order = self.env['sale.order'].browse(res['sale_order_id'])
            preferred_journal = self.env['account.journal'].search([
                ('type', 'in', ['cash', 'bank']),
                ('preferred_method', '=', True)
            ], limit=1)
            if not preferred_journal:
                preferred_journal = self.env['account.journal'].search([
                    ('type', 'in', ['cash', 'bank'])
                ], limit=1)
            if preferred_journal and 'payment_line_ids' in fields:
                res['payment_line_ids'] = [(0, 0, {
                    'journal_id': preferred_journal.id,
                    'amount': sale_order.amount_total
                })]
        return res

    def action_confirm_payments(self):
        self.ensure_one()

        # Validar que el total pagado sea igual al total del pedido
        if self.amount_due != 0:
            if self.amount_due > 0:
                raise UserError(_('El monto total pagado (S/%.2f) es menor que el total del pedido (S/%.2f). Faltan S/%.2f por cubrir.') % (self.amount_paid, self.amount_total, self.amount_due))
            else:
                raise UserError(_('El monto total pagado (S/%.2f) excede el total del pedido (S/%.2f). Sobran S/%.2f.') % (self.amount_paid, self.amount_total, -self.amount_due))

        # Confirmar el pedido de venta
        self.sale_order_id.with_context(skip_payment_wizard=True).action_confirm()

        # Eliminar las líneas de pago existentes (si las hay)
        self.sale_order_id.payment_line_ids.unlink()

        # Crear líneas de pago en el pedido de venta
        for line in self.payment_line_ids:
            self.env['sale.order.payment.line'].create({
                'sale_order_id': self.sale_order_id.id,
                'journal_id': line.journal_id.id,
                'amount': line.amount
            })

        # Crear y conciliar los pagos automáticamente si auto_pay está activado
        if self.sale_order_id.auto_pay and self.sale_order_id.payment_line_ids:
            if self.sale_order_id.auto_invoice:
                # Verificar si se creó una factura
                invoice = self.sale_order_id.invoice_ids.filtered(lambda inv: inv.state == 'posted')[:1]
                if not invoice:
                    raise UserError(_('No se encontró una factura publicada para conciliar los pagos. Asegúrese de que auto_invoice esté activado y que la factura se haya creado y publicado correctamente.'))
                
                # Crear y conciliar pagos con la factura
                for payment_line in self.sale_order_id.payment_line_ids:
                    payment_wizard_action = invoice.action_register_payment()
                    payment_wizard_model = payment_wizard_action.get('res_model')
                    payment_wizard_context = payment_wizard_action.get('context', {})
                    payment_wizard = self.env[payment_wizard_model].with_context(payment_wizard_context).create({
                        'amount': payment_line.amount,
                        'journal_id': payment_line.journal_id.id,
                        'payment_date': fields.Date.today(),
                        'communication': f'Pago desde orden de venta {self.sale_order_id.name} - {payment_line.journal_id.name}',
                    })
                    payment_wizard.action_create_payments()
            else:
                # Si auto_invoice está desactivado, crear pagos directamente sin conciliar con factura
                for payment_line in self.sale_order_id.payment_line_ids:
                    payment = self.env['account.payment'].create({
                        'amount': payment_line.amount,
                        'journal_id': payment_line.journal_id.id,
                        'date': fields.Date.today(),
                        'payment_type': 'inbound',
                        'partner_id': self.sale_order_id.partner_id.id,
                        'partner_type': 'customer',
                        'memo': f'Pago desde orden de venta {self.sale_order_id.name} - {payment_line.journal_id.name}',
                        'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
                    })
                    payment.action_post()

        return True

class SaleOrderPaymentWizardLine(models.TransientModel):
    _name = 'sale.order.payment.wizard.line'
    _description = 'Línea de Pago de Wizard'

    wizard_id = fields.Many2one('sale.order.payment.wizard', string='Wizard', required=True, ondelete='cascade')
    journal_id = fields.Many2one(
        'account.journal',
        string='Método de Pago',
        domain=[('type', 'in', ['cash', 'bank'])],
        required=True
    )
    amount = fields.Monetary(string='Monto', required=True)
    currency_id = fields.Many2one('res.currency', related='wizard_id.currency_id')

    @api.model
    def create(self, vals):
        wizard = self.env['sale.order.payment.wizard'].browse(vals['wizard_id'])
        wizard._compute_amount_paid()
        wizard._compute_amount_due()
        if wizard.amount_due <= 0 and vals.get('amount', 0) > 0:
            raise UserError(_('El saldo pendiente ya es 0. No se pueden añadir más líneas de pago con monto mayor a 0.'))
        return super(SaleOrderPaymentWizardLine, self).create(vals)

    @api.model
    def default_get(self, fields):
        res = super(SaleOrderPaymentWizardLine, self).default_get(fields)
        if 'wizard_id' in res:
            wizard = self.env['sale.order.payment.wizard'].browse(res['wizard_id'])
            wizard._compute_amount_paid()
            wizard._compute_amount_due()
            journal = self.env['account.journal'].search([
                ('type', 'in', ['cash', 'bank']),
                ('preferred_method', '=', True),
                ('id', 'not in', wizard.payment_line_ids.mapped('journal_id').ids)
            ], limit=1)
            if not journal:
                journal = self.env['account.journal'].search([
                    ('type', 'in', ['cash', 'bank']),
                    ('id', 'not in', wizard.payment_line_ids.mapped('journal_id').ids)
                ], limit=1)
            if journal:
                res['journal_id'] = journal.id
            # Precargar el monto con el saldo pendiente actual
            res['amount'] = max(wizard.amount_due, 0)  # Asegurarse de que no sea negativo
        return res

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        """Precargar el monto con el saldo pendiente cuando se selecciona un método de pago"""
        if self.wizard_id and not self.amount:
            self.wizard_id._compute_amount_paid()
            self.wizard_id._compute_amount_due()
            self.amount = max(self.wizard_id.amount_due, 0)

    @api.constrains('amount')
    def _check_amount(self):
        for line in self:
            if line.amount < 0:
                raise ValidationError(_('El monto de una línea de pago no puede ser negativo.'))
            total_paid = sum(line.wizard_id.payment_line_ids.mapped('amount'))
            if total_paid > line.wizard_id.amount_total:
                raise ValidationError(_('El monto total pagado (S/%.2f) no puede exceder el total del pedido (S/%.2f).') % (total_paid, line.wizard_id.amount_total))

    @api.onchange('amount')
    def _onchange_amount(self):
        if self.wizard_id:
            self.wizard_id._compute_amount_paid()
            self.wizard_id._compute_amount_due()
        return {'value': {'amount': self.amount}}