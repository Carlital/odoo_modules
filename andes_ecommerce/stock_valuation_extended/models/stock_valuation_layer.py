from odoo import models, fields

class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'
    lot_number = fields.Char(
        related='stock_move_id.move_line_ids.lot_id.name',
        string="Lote",
        store=True,
        readonly=True
    )
    expiration_date = fields.Datetime(
        related='stock_move_id.move_line_ids.lot_id.expiration_date',
        string="Fecha de Caducidad",
        store=True,
        readonly=True
    )
