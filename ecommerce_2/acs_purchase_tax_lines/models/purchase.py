from odoo import fields, models, api
import logging
_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    tax_ids = fields.Many2many(
        'account.tax',
        string="Impuestos",
        domain="[('type_tax_use', '=', 'purchase')]"
    )

    general_taxes = fields.Boolean(
        string="Impuestos Generales",
        default=False
    )

    @api.onchange('tax_ids')
    def _onchange_tax_ids(self):
        
        for order in self:
            if order.tax_ids:
                for line in order.order_line:
                    line.taxes_id = [(6, 0, order.tax_ids.ids)]