from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    allow_picking_conversion = fields.Boolean(
        string='Conversiones Picking',
        default=False,
        help='Permite al usuario realizar conversiones de picking de peso a metros'
    )
