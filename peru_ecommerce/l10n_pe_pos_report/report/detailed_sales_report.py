# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import UserError
import json
from odoo.tools.misc import formatLang, format_date, get_lang

class PosInvoiceReport(models.AbstractModel):
    _name = 'report.l10n_pe_pos_report.report_detailed_sales_report'
    _description = 'Session Detailed Sales Report'


    @api.model
    def _get_report_values(self, docids, data=None):
        values = {}
        docs = self.env['pos.session'].browse(docids)
        for session_id in self.env['pos.session'].browse(docids):
            lines = []
            base_exo =0.0
            base_ina = 0.0
            base_igv = 0.0
            base_exp = 0.0
            igv = 0.0
            total = 0.0
            order_ids = self.env['pos.order'].search([('session_id','=',session_id.id)], order="pe_move_name ASC")
            for order_id in order_ids:
                vals = {}
                sign = order_id.amount_total/abs(order_id.amount_total)
                vals['invoice_date'] = format_date(order_id.env, order_id.account_move.invoice_date)
                vals['name'] = order_id.account_move.name
                vat = order_id.partner_id.vat
                partner = vat and "%s - %s" %(vat, order_id.partner_id.name) or order_id.partner_id.name
                vals['partner'] = partner
                invoice_line_ids = order_id.account_move.invoice_line_ids
                vals['amount_exo'] = formatLang(self.env, sign*sum(invoice_line_ids.filtered(lambda s: s.pe_type_affectation=='20').mapped('price_subtotal')))
                vals['amount_ina'] = formatLang(self.env, sign*sum(invoice_line_ids.filtered(lambda s: s.pe_type_affectation=='30').mapped('price_subtotal')))
                vals['amount_igv'] = formatLang(self.env, sign*sum(invoice_line_ids.filtered(lambda s: s.pe_type_affectation=='10').mapped('price_subtotal')))
                vals['amount_exp'] = formatLang(self.env, sign*sum(invoice_line_ids.filtered(lambda s: s.pe_type_affectation=='40').mapped('price_subtotal')))
                vals['igv'] = formatLang(self.env, order_id.account_move.amount_tax_signed)
                vals['amount'] = formatLang(self.env, order_id.amount_total)
                base_exo += sign*sum(invoice_line_ids.filtered(lambda s: s.pe_type_affectation=='20').mapped('price_subtotal'))
                base_ina += sign*sum(invoice_line_ids.filtered(lambda s: s.pe_type_affectation=='30').mapped('price_subtotal'))
                base_igv += sign*sum(invoice_line_ids.filtered(lambda s: s.pe_type_affectation=='10').mapped('price_subtotal'))
                base_exp += sign*sum(invoice_line_ids.filtered(lambda s: s.pe_type_affectation=='40').mapped('price_subtotal'))
                igv += order_id.account_move.amount_tax_signed
                total += order_id.amount_total
                lines.append(vals)
            values[session_id.id] = {}
            values[session_id.id]['lines'] = lines
            values[session_id.id]['base_exo'] = formatLang(self.env, base_exo)
            values[session_id.id]['base_ina'] = formatLang(self.env, base_ina)
            values[session_id.id]['base_igv'] = formatLang(self.env, base_igv)
            values[session_id.id]['base_exp'] = formatLang(self.env, base_exp)
            values[session_id.id]['igv'] = formatLang(self.env, igv)
            values[session_id.id]['total'] = formatLang(self.env, total)
            query = """(SelECT SUM(am.amount_total_signed) AS amount_total, aj.name AS name FROM 
            account_move AS am INNER JOIN account_journal AS aj ON am.journal_id=aj.id 
            WHERE am.id IN (select account_move from pos_order WHERE session_id=%s and account_move IS NOT NULL) 
            GROUP BY aj.name ORDER BY aj.name ASC)
            UNION
            (select SUM(amount_total) as amount_total, 'Ticket' AS name 
            FROM pos_order WHERE account_move IS NULL AND session_id=%s)"""
            self.env.cr.execute(query, [session_id.id, session_id.id])
            total_vals = self.env.cr.dictfetchall()
            totals = []
            amount_total = 0.0
            for total_val in total_vals:
                if total_val.get('amount_total'):
                    totals.append({
                        'name': total_val.get('name'),
                        'amount_total': formatLang(self.env, total_val.get('amount_total')),
                    })
                    amount_total+=total_val.get('amount_total')
            values[session_id.id]['totals'] = totals
            values[session_id.id]['amount_total'] = formatLang(self.env, amount_total)

        return {
            "docs": docs,
            "data": values,
            "formatLang":formatLang
        }
