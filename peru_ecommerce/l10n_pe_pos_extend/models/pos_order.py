# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime

class PosOrder(models.Model):
    _inherit = "pos.order"
    
    def _prepare_invoice_vals(self):
        res = super(PosOrder, self)._prepare_invoice_vals()
        return res

    def _export_for_ui(self, order):
        res = super(PosOrder, self)._export_for_ui(order)
        res['invoice_date'] = order.account_move.invoice_date and fields.Date.to_string(order.account_move.invoice_date) or False
        return res

