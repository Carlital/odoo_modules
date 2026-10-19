from odoo import api, fields, models
from odoo.exceptions import ValidationError


class BillingActivity(models.Model):
    _name = "billing.activity"
    _description = "Actividad de Facturacion"
    _order = "ruc, name"

    name = fields.Char(required=True)
    code = fields.Char(help="Codigo interno opcional para mapear desde Excel")
    ruc = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    owner_user_id = fields.Many2one("res.users", string="Usuario", index=True)

    _sql_constraints = [
        (
            "billing_activity_code_unique",
            "unique(code)",
            "El codigo de actividad debe ser unico.",
        )
    ]

    @api.constrains("ruc", "owner_user_id")
    def _check_ruc_single_user(self):
        for activity in self:
            if not activity.owner_user_id:
                raise ValidationError("Debe indicar el usuario propietario de la actividad.")
            if not activity.ruc:
                continue
            same_ruc_activities = self.search([
                ("ruc", "=", activity.ruc),
                ("id", "!=", activity.id),
            ])
            foreign_owner = same_ruc_activities.filtered(
                lambda rec: rec.owner_user_id and rec.owner_user_id != activity.owner_user_id
            )
            if foreign_owner:
                raise ValidationError(
                    "El RUC %s ya esta asignado a otro usuario. Un RUC solo puede pertenecer a un usuario."
                    % activity.ruc
                )

            owner_other_ruc = self.search([
                ("owner_user_id", "=", activity.owner_user_id.id),
                ("id", "!=", activity.id),
                ("ruc", "!=", activity.ruc),
            ], limit=1)
            if owner_other_ruc:
                raise ValidationError(
                    "El usuario %s ya tiene actividades con otro RUC. Cada usuario debe manejar un unico RUC."
                    % activity.owner_user_id.display_name
                )
