# -*- coding: utf-8 -*-

from odoo import api, models, fields, tools, _
from odoo.exceptions import UserError
import base64
import re
from datetime import datetime
from librecpe.cpe import Cliente
import requests

class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    
    def _check_move_configuration(self, move):
        self.ensure_one()
        if self.code != 'pe_cpe':
            return super(AccountEdiFormat, self)._check_move_configuration(move)
        res = super(AccountEdiFormat, self)._check_move_configuration(move)
        company_id = move.company_id.parent_id or move.company_id


        if move.pe_invoice_code in ['03'] or move.reversed_entry_id.pe_invoice_code in ['03'] or move.debit_origin_id.pe_invoice_code in ['03']:
            amount = company_id.pe_max_amount or 0
            if move.amount_total > amount and move.partner_id.id == self.env.ref('l10n_pe_pos.partner_pe_cf').id:
                res.append("El cliente debe tener un numero de documento de identidad valido")
        return res
            
        