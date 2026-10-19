from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    acs_po_no_confirm = fields.Boolean(
        string="No se permite confirmar compra", default=False)
