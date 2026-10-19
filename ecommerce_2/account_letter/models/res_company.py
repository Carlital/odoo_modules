# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class ResCompany(models.Model):
    _inherit = "res.company"

    letters_portfolio_account_id = fields.Many2one("account.account", "Letter Portfolio Account", domain = lambda self: [('reconcile', '=', True), ('deprecated', '=', False)])
    letters_payment_account_id = fields.Many2one("account.account", "Letter Payment Account", domain = lambda self: [('reconcile', '=', True), ('deprecated', '=', False)])
    letters_payable_account_id = fields.Many2one("account.account", "Letter Payable Account", domain = lambda self: [('reconcile', '=', True), ('deprecated', '=', False)])