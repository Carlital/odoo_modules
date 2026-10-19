
from odoo import api, fields, models

class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    immediate = fields.Boolean('Inmediato')

