
from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    journal_id = fields.Many2one(
        'account.journal', string='Metodo de pago',
        domain="[('type', 'in', ('cash', 'bank'))]")

    immediate = fields.Boolean(
        related='payment_term_id.immediate', string='Inmediato')
