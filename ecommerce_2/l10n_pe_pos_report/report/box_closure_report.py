# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import UserError
import json
from odoo.tools.misc import formatLang, format_date, get_lang, format_datetime

class BoxClosureReport(models.AbstractModel):
    _name = 'report.l10n_pe_pos_report.report_box_closure_report'
    _description = 'Closure Box Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        values = {}
        docs = self.env['pos.session'].browse(docids)

        for session_id in self.env['pos.session'].browse(docids):
            lines = []
            payment_ids = self.env['pos.payment'].search([('session_id','=',session_id.id)], order="payment_method_id ASC, payment_date ASC")
            amount_total = 0.0
            for payment_id in payment_ids:
                vals = {}
                vals['payment_date'] = format_datetime(self.env, payment_id.payment_date)
                vals['name'] = payment_id.payment_method_id.name
                vals['amount'] =  formatLang(self.env, payment_id.amount)
                lines.append(vals)
                amount_total+=  payment_id.amount
            query = """SELECT SUM(pos_payment.amount) AS amount_total, pos_payment_method.name 
            FROM pos_payment INNER JOIN pos_payment_method ON pos_payment.payment_method_id=pos_payment_method.id 
            WHERE session_id = %s GROUP BY pos_payment_method.name ORDER BY pos_payment_method.name ASC;"""
            self.env.cr.execute(query, [session_id.id])
            total_vals = self.env.cr.dictfetchall()
            totals = []
            for total_val in total_vals:
                if total_val.get('amount_total'):
                    totals.append({
                        'name': total_val.get('name'),
                        'amount_total': formatLang(self.env, total_val.get('amount_total')),
                    })
            values[session_id.id] = {}
            values[session_id.id]['lines'] = lines
            values[session_id.id]['totals'] = totals
            values[session_id.id]['amount_total'] = formatLang(self.env, amount_total)

        return {
            "docs": docs,
            "data": values,
            "formatLang":formatLang
        }
