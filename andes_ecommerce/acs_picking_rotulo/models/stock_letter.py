# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import AccessDenied

class AccountLetter(models.Model):
    _inherit = 'stock.picking'
    
    is_sent = fields.Boolean(string="Enviado", default=False)
        
    def toggle_sent(self):
        if self.is_sent:
            self.is_sent= False
        else:
            self.is_sent= True

    def print_pdf_letter(self):
        self.ensure_one()
        self.is_sent = True
        if self.partner_id:
            return self.env.ref('acs_picking_rotulo.pdf_stock_letter_report').report_action(self)
        else:
            raise AccessDenied(('No partner assigned'))
            