
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    profit_percentage_pu = fields.Char('% PU')
    profit_percentage_pm = fields.Char('% PM')
    profit_percentage_pc = fields.Char('% PC')
