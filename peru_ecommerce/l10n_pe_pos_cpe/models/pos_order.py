# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime
import pytz

class PosOrder(models.Model):
    _inherit = "pos.order"

    pe_journal_id = fields.Many2one('account.journal', string='Invoice Journal',
                                       domain="[('type', 'in', ['sale']),('company_id','=',company_id)]", copy=True)
    pe_move_name = fields.Char(string='Move Name', readonly=True, copy=False)
    pe_credit_note_code = fields.Selection(selection="_get_pe_credit_note_type", string="Credit Note Code")
    pe_annul = fields.Boolean("Annul")

    def refund(self):
        res = super(PosOrder, self).refund()
        if res.get('res_id') and self:
            order_id = self.browse(res.get('res_id'))
            order_id.pe_journal_id = self[0].pe_journal_id.pe_credit_note_id.id or self[0].pe_journal_id.id
            order_id.pe_credit_note_code = '01'
        return res

    def _create_invoice(self, move_vals):
        res = super(PosOrder, self)._create_invoice(move_vals)
        return res

    @api.model
    def _get_pe_credit_note_type(self):
        return self.env['pe.catalog.09'].get_selection()

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res['pe_move_name']=ui_order.get('pe_move_name', False)
        res['pe_journal_id']=ui_order.get('pe_journal_id', False)
        res['pe_credit_note_code'] = ui_order.get("pe_credit_note_code", False)
        if ui_order.get('pe_journal_id', False):
            res['to_invoice'] = True
        return res

    def _prepare_invoice_vals(self):
        res = super(PosOrder, self)._prepare_invoice_vals()
        if self.pe_credit_note_code:
            res['pe_credit_note_code'] = self.pe_credit_note_code
        if self.refunded_order_ids:
            res['reversed_entry_id'] = self.refunded_order_ids and self.refunded_order_ids[0].account_move.id or False
            if not self.pe_credit_note_code:
                res['pe_credit_note_code'] = '07'
            if res['reversed_entry_id']:
                res['invoice_origin'] = self.refunded_order_ids and self.refunded_order_ids[0].account_move.l10n_latam_document_number or False
        if self.pe_move_name:
            res['l10n_latam_document_number'] = self.pe_move_name
        if self.pe_journal_id:
            res['journal_id'] = self.pe_journal_id.id
            l10n_latam_document_type_id = self.env['l10n_latam.document.type'].search([('code', '=', self.pe_journal_id.pe_invoice_code)], limit=1)
            res['l10n_latam_document_type_id'] = l10n_latam_document_type_id.id
        return res

    def _export_for_ui(self, order):
        res = super(PosOrder, self)._export_for_ui(order)
        res['pe_journal_id'] = order.pe_journal_id.id
        res['pe_move_name'] = order.pe_move_name
        res['pe_credit_note_code'] = order.pe_credit_note_code
        res['pe_src_move_name'] = order.account_move.reversed_entry_id.l10n_latam_document_number
        return res

    def get_pe_invoice_from_ui(self):
        self.ensure_one()
        vals = {}
        name = ''
        if self.account_move.pe_invoice_code in ['01']:
            name+='Factura '
        if self.account_move.pe_invoice_code in ['03']:
            name+='Boleta de venta '
        if self.account_move.pe_invoice_code in ['07']:
            name+='Nota de crédito '
        if self.account_move.pe_invoice_code in ['08']:
            name+='Nota de débito '
        if self.account_move.pe_is_cpe:
            name+='Electrónica'
        vals['pe_move_name'] = self.account_move.name
        vals['pe_invoice_name'] = name
        if self.account_move.pe_is_cpe:
            vals['pe_qr_code'] = 'data:image/png;base64,%s' % str(self.account_move.pe_qr_code)
        else:
            vals['pe_qr_code'] = False
        return vals

    def refund(self):
        res = super(PosOrder, self).refund()
        if res.get('res_id') and self:
            order_id = self.browse(res.get('res_id'))
            order_id.pe_journal_id = self[0].pe_journal_id.pe_credit_note_id.id or self[0].pe_journal_id.id
            # order_id.reversed_order_id = self[0].id
        return res

    def action_annul(self):
        refund_orders = self.env['pos.order']
        for order in self:
            current_session = order.session_id.config_id.current_session_id
            if not current_session:
                raise ValidationError(
                    _('To return product(s), you need to open a session in the POS %s') % order.session_id.config_id.display_name)
            refund_order = order.copy({
                'name': order.name + _(' ANNUL'),
                'session_id': current_session.id,
                'date_order': fields.Datetime.now(),
                'pos_reference': order.pos_reference,
                'lines': False,
                'amount_tax': -order.amount_tax,
                'amount_total': -order.amount_total,
                'amount_paid': 0,
                'reversed_order_id': order.id,
                'reversed_entry_id': False,
                'pe_journal_id': False,
                'pe_annul': True,
            })
            for line in order.lines:
                PosOrderLineLot = self.env['pos.pack.operation.lot']
                for pack_lot in line.pack_lot_ids:
                    PosOrderLineLot += pack_lot.copy()
                line.copy({
                    'name': line.name + _(' ANNUL'),
                    'qty': -line.qty,
                    'order_id': refund_order.id,
                    'price_subtotal': -line.price_subtotal,
                    'price_subtotal_incl': -line.price_subtotal_incl,
                    'pack_lot_ids': PosOrderLineLot,
                })
            refund_orders |= refund_order

        return {
            'name': _('Return Products'),
            'view_mode': 'form',
            'res_model': 'pos.order',
            'res_id': refund_orders.ids[0],
            'view_id': False,
            'context': self.env.context,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    # def _process_saved_order(self, draft):
    #     res = super(PosOrder, self)._process_saved_order(draft)
    #     if self.pe_journal_id and self.state == 'paid':
    #         self._generate_pos_order_invoice()
    #     return res

    def _create_invoice(self, move_vals):
        new_move = super(PosOrder, self)._create_invoice(move_vals)
        for line in new_move.invoice_line_ids:
            if line.discount==100:
                tax_id = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', '9998'), ('type_tax_use', '=', 'sale'),
                                                        ('company_id', '=', line.move_id.company_id.id)], limit=1)
                if tax_id:
                    line.tax_ids = line.tax_ids.ids + tax_id.ids
            pe_type_affectation = line._get_pe_type_affectation_by_tax()
            line.pe_type_affectation = pe_type_affectation
        return new_move