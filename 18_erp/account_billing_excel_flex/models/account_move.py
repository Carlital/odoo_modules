from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    activity_id = fields.Many2one(
        "billing.activity",
        string="Actividad",
        default=lambda self: self.env.user.invoice_activity_id.id,
    )
    activity_ruc = fields.Char(related="activity_id.ruc", string="RUC Actividad", store=True, index=True)
