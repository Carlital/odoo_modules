# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
import requests
from datetime import datetime, timedelta
import re

class AccountInvoice(models.Model):
    _inherit = 'account.move'

    pe_cpe_state = fields.Selection(selection=[('0', 'No Existe'),
                                               ('1', 'Aceptado'),
                                               ('2', 'Anulado'),
                                               ('3', 'Autorizado'),
                                               ('4', 'No Autorizado')], string="CPE State", readolny=True)

    def _get_pe_cpe_state(self):
        for move_id in self.filtered(lambda s: s.state in ['posted', 'cancel'] and s.name != '/'):
            if move_id.company_id.account_fiscal_country_id.code != 'PE':
                continue
            if not move_id.l10n_latam_document_type_id:
                continue
            if move_id.l10n_latam_document_type_id.code not in ['01', '03', '04', '07', '08']:
                continue
            if move_id.move_type in ['in_invoice', 'in_refund'] and move_id.partner_id.pe_doc_type in ['6'] and move_id.partner_id.vat:
                move_name = move_id.ref or move_id.l10n_latam_document_number
                ruc = move_id.partner_id.vat
            else:
                ruc = move_id.company_id.vat
                move_name = move_id.name.replace(" ","")
            if not move_name or not ruc:
                continue
            check_move_name = re.findall(r'^.*([A-Z0-9]{4})-(\d{1,8})$', move_name)
            if check_move_name and ruc and move_id.l10n_latam_document_type_id.code:
                data = {
                    "ruc": ruc,
                    "document_code": move_id.l10n_latam_document_type_id.code,
                    "serie": check_move_name[0][0],
                    "number": check_move_name[0][1],
                    "date": fields.Date.to_string(move_id.invoice_date),
                    "amount": move_id.amount_total,
                }
                token = self.env['ir.config_parameter'].sudo().get_param('l10n_pe_vat.token') or self.env['ir.config_parameter'].sudo().get_param('l10n_pe_cpe_check.token')
                if token:
                    headers = {'Authorization': 'Bearer %s' % token,
                               'Content-type': 'application/json'}
                else:
                    headers = {'Content-type': 'application/json'}
                res = requests.post('https://api.mifactura.digital/v2/invoice/', json=data, headers=headers)
                if res.status_code == 200:
                    move_id.pe_cpe_state = res.json().get('state')
                    self.env.cr.commit()
        return {}

    @api.model
    def check_pe_cpe_state(self, days=30, limit=30, start_date=False, end_date=False):
        if not start_date:
            start_date = fields.Date.to_string(datetime.now() - timedelta(days=days))
        if not end_date:
            end_date = fields.Date.to_string(datetime.now() - timedelta(days=2))
        move_ids = self.search([('pe_cpe_state', '=', False),
                                ('state', 'in', ['posted', 'cancel']), ('invoice_date','<=',end_date),
                                ('invoice_date','>=',start_date), ('l10n_latam_document_type_id', '!=', False),
                                ('company_id.account_fiscal_country_id.code','=','PE'),
                                ('move_type','in',['out_invoice','out_refund','in_invoice','in_refund'])],
                               limit=limit, order='invoice_date asc')

        return move_ids._get_pe_cpe_state()