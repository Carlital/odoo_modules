from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    acs_hide_prices = fields.Boolean(
        string='Ocultar precios de productos',
        help='Si está marcado, este usuario no podrá ver los precios de los productos en el sistema'
    )
