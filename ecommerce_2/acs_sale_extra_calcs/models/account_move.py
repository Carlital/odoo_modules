from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    acs_cant_pzs = fields.Float(
        string='Cant. Pzas',
        digits='Product Unit of Measure'
    )
    acs_udv = fields.Many2one(
        'uom.uom',
        string='Udv',
        help='Unidad de medida informativa, no afecta los cálculos'
    )
    acs_largue_pza = fields.Float(
        string='Largo x Pza - mts',
        digits='Product Unit of Measure'
    )
    acs_price_pza = fields.Float(
        string='Prec. x Pza',
        digits='Product Price'
    )
