from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    ver_boton_crear_guias = fields.Boolean(
        string='Ver botón crear guías',
        default=False,
        help="Si está activado, el usuario podrá ver el botón para crear nuevas guías electrónicas."
    )
