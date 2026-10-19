
from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    brand_id = fields.Many2one(
        'brand.comercial.tours',
        string='Marca')
