from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    secondary_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        related='product_id.secondary_uom_id',
        string='UoM 2',
        readonly=True,
        store=True
    )

    conversion_ratio = fields.Float(
        related='product_id.conversion_ratio',
        string='Relación de Conversión',
        readonly=True,
        store=True
    )

    secondary_qty = fields.Float(
        string='Cant. 2',
        compute='_compute_secondary_qty',
        store=True,
        readonly=True,
        help="Cantidad calculada en la unidad de medida secundaria"
    )

    @api.depends('product_uom_qty', 'conversion_ratio')
    def _compute_secondary_qty(self):
        for line in self:
            line.secondary_qty = line.product_uom_qty * line.conversion_ratio
