from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    invoice_line_pdesc = fields.Float(
        string='P.Unit. Desc',
        compute='_compute_line_pdesc',
        readonly=True,
        store=False,
    )

    @api.depends('price_unit', 'discount')
    def _compute_line_pdesc(self):
        for line in self:
            # Calcular precio unitario con descuento: precio - (descuento % * precio)
            discount = line.discount or 0.0
            line.invoice_line_pdesc = line.price_unit * (1 - discount / 100.0)