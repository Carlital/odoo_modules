from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    website_analytic_id = fields.Many2one(
        'account.analytic.account',
        related='company_id.website_analytic_id',
        string = 'Cuenta analitica Website',
        store = True,
        readonly=False,
    )