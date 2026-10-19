# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    stock_condition = fields.Char(
        string='Condición de Stock',
        compute='_compute_stock_condition',
        store=True,
        readonly=True,
    )

    @api.depends('product_id', 'order_id.partner_id')
    def _compute_stock_condition(self):
        for line in self:
            if line.product_id and line.order_id.partner_id:
                seller = line.product_id._select_seller(
                    partner_id=line.order_id.partner_id,
                    quantity=line.product_qty,
                    date=line.order_id.date_order and line.order_id.date_order.date(),
                    uom_id=line.product_uom)
                line.stock_condition = seller.stock_condition if seller else False
            else:
                line.stock_condition = False
