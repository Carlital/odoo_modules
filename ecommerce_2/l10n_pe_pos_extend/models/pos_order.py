# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
import pytz

class PosOrder(models.Model):
    _inherit = "pos.order"

    pe_invoice_date = fields.Date(string='Invoice Date (PE)', compute='_compute_pe_invoice_date', store=True)

    @api.depends('date_order')
    def _compute_pe_invoice_date(self):
        for order in self:
            timezone = pytz.timezone('America/Lima')
            invoice_date = order.date_order
            order.pe_invoice_date = invoice_date.astimezone(timezone)

    def _prepare_invoice_vals(self):
        res = super(PosOrder, self)._prepare_invoice_vals()
        return res

    def _export_for_ui(self, order):
        res = super(PosOrder, self)._export_for_ui(order)
        res['invoice_date'] = order.account_move.invoice_date and fields.Date.to_string(order.account_move.invoice_date) or False
        res['pe_invoice_date'] = order.pe_invoice_date
        return res

