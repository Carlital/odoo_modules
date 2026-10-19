# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    available_lot_id = fields.Many2one(
        'stock.lot',
        string='Lote/Serie disponible',
        help='Lote/serie con stock disponible para selección.',
        store=False,
    )

    @api.onchange('available_lot_id')
    def _onchange_available_lot_id(self):
        for move in self:
            if move.available_lot_id:
                # Asignar el producto del lote seleccionado
                move.product_id = move.available_lot_id.product_id
                # move.lot_ids = [(6, 0, [move.available_lot_id.id])]
