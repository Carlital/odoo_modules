from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    website_analytic_id = fields.Many2one(
        'account.analytic.account',
        string = 'Cuenta analítica Website',
        store = True,
        readonly=False,
    )