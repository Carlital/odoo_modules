from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = "res.users"

    billing_activity_ids = fields.One2many("billing.activity", "owner_user_id", string="Actividades de Facturacion")
    invoice_activity_id = fields.Many2one(
        "billing.activity",
        string="Actividad activa en Facturacion",
        domain="[('id', 'in', billing_activity_ids)]",
    )
    invoice_activity_option = fields.Selection(
        selection="_selection_activity_options",
        string="Actividad a visualizar",
        compute="_compute_invoice_activity_option",
        inverse="_inverse_invoice_activity_option",
        help="Selector rapido en formato radio para elegir la actividad visible en facturacion.",
    )

    @api.model
    def _selection_activity_options(self):
        options = []
        for activity in self.env.user.billing_activity_ids:
            options.append((str(activity.id), "%s (%s)" % (activity.name, activity.ruc)))
        return options

    @api.depends("invoice_activity_id")
    def _compute_invoice_activity_option(self):
        for user in self:
            user.invoice_activity_option = str(user.invoice_activity_id.id) if user.invoice_activity_id else False

    def _inverse_invoice_activity_option(self):
        for user in self:
            user.invoice_activity_id = int(user.invoice_activity_option) if user.invoice_activity_option else False

    @api.onchange("billing_activity_ids")
    def _onchange_billing_activity_ids(self):
        for user in self:
            if user.invoice_activity_id and user.invoice_activity_id not in user.billing_activity_ids:
                user.invoice_activity_id = False
            if not user.invoice_activity_id and user.billing_activity_ids:
                user.invoice_activity_id = user.billing_activity_ids[0]

    @api.constrains("billing_activity_ids", "invoice_activity_id", "groups_id")
    def _check_activity_requirements(self):
        restricted_group = self.env.ref("account_billing_excel_flex.group_activity_restricted_invoice_view", raise_if_not_found=False)
        for user in self:
            if not restricted_group or restricted_group not in user.groups_id:
                continue
            if not user.billing_activity_ids:
                raise ValidationError(_("El usuario debe tener al menos una actividad de facturacion."))
            if not user.invoice_activity_id:
                raise ValidationError(_("Debe seleccionar una actividad activa en facturacion."))
            if user.invoice_activity_id and user.invoice_activity_id not in user.billing_activity_ids:
                raise ValidationError(_("La actividad activa debe pertenecer al usuario."))

    def write(self, vals):
        result = super().write(vals)
        restricted_group = self.env.ref("account_billing_excel_flex.group_activity_restricted_invoice_view", raise_if_not_found=False)
        for user in self:
            if restricted_group and restricted_group in user.groups_id and not user.invoice_activity_id and user.billing_activity_ids:
                user.invoice_activity_id = user.billing_activity_ids[0]
        return result
