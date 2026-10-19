from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    auto_sign_on_order_production = fields.Boolean(
        string="Firma Automática en Orden de Producción",
        help="Si está marcado, la firma de este usuario se agregará automáticamente en los reportes de orden de producción.",
        copy=False
    )

    @api.constrains('auto_sign_on_order_production')
    def _check_unique_auto_sign_on(self):
        """
        Asegura que solo un usuario pueda tener el campo
        'auto_sign_on_order_production' activado.
        """
        for user in self.filtered('auto_sign_on_order_production'):
            other_user = self.search([
                ('id', '!=', user.id),
                ('auto_sign_on_order_production', '=', True)
            ], limit=1)
            if other_user:
                raise ValidationError(_(
                    "Solo un usuario puede tener la 'Firma Automática' activa. El usuario '%s' ya tiene esta opción habilitada.",
                    other_user.name
                ))
