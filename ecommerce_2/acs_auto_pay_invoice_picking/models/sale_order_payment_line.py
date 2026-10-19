from odoo import api, fields, models

class SaleOrderPaymentLine(models.Model):
    _name = 'sale.order.payment.line'
    _description = 'Líneas de pago de pedido de venta'

    sale_order_id = fields.Many2one('sale.order', string='Pedido de Venta', required=True, ondelete='cascade')
    journal_id = fields.Many2one(
        'account.journal',
        string='Método de Pago',
        domain=[('type', 'in', ['cash', 'bank'])],
        required=True
    )
    amount = fields.Monetary(string='Monto', required=True)
    currency_id = fields.Many2one(
        'res.currency', 
        string='Moneda',
        related='sale_order_id.currency_id', 
        store=True
    )
    name = fields.Char(string='Descripción', compute='_compute_name')

    @api.depends('journal_id', 'amount')
    def _compute_name(self):
        for line in self:
            if line.journal_id and line.amount:
                line.name = f"{line.journal_id.name}: {line.amount}"
            else:
                line.name = "Método de pago"