# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _compute_valorizado_total(self):
        for r in self:
            r.valorizado_total = sum(r.move_ids_without_package.mapped('line_valorizado'))

    currency_id = fields.Many2one("res.currency", string="Valuta", related='company_id.currency_id')


    valorizado_total = fields.Monetary(
        string='Valorizado total',
        compute="_compute_valorizado_total"
    )

    

class StockMove(models.Model):
    _inherit = 'stock.move'


    def _compute_valorizado_line(self):
        for r in self:
            r.line_valorizado = r.product_id.standard_price * r.quantity

    line_valorizado = fields.Float(
        string='Linea Valorizado',
        compute="_compute_valorizado_line"
    )
    