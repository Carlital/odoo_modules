# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class AccoutMoveLine(models.Model):
    _inherit = 'account.move.line'

    pe_prepaid_invoice_id = fields.Many2one("account.move", compute="_compute_pe_prepaid_invoice_id", store=True, readonly=False)

    @api.depends('sale_line_ids')
    def _compute_pe_prepaid_invoice_id(self):
        for line in self:
            if line.quantity<0.0:
                invoice_lines = line.sale_line_ids.mapped('invoice_lines').filtered(lambda l: l.id!=line.id and round(l.move_id.amount_total,2) == round(l.price_total,2) and l.move_id.state == 'posted')
                line.pe_prepaid_invoice_id = invoice_lines and invoice_lines[0].move_id.id or False
            else:
                line.pe_prepaid_invoice_id = False