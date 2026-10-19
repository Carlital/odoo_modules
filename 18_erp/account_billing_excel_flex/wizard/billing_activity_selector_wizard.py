from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class BillingActivitySelectorWizard(models.TransientModel):
    _name = "billing.activity.selector.wizard"
    _description = "Selector de actividad de facturacion"

    activity_id = fields.Many2one(
        "billing.activity",
        string="Actividad",
        required=True,
        domain="[('owner_user_id', '=', uid)]",
    )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if "activity_id" in fields_list and self.env.user.invoice_activity_id:
            values["activity_id"] = self.env.user.invoice_activity_id.id
        return values

    def action_apply(self):
        self.ensure_one()
        if not self.activity_id:
            raise ValidationError(_("Debe seleccionar una actividad."))
        self.env.user.invoice_activity_id = self.activity_id.id
        return {
            "type": "ir.actions.act_window",
            "name": _("Facturas"),
            "res_model": "account.move",
            "view_mode": "list,form",
            "domain": [
                ("move_type", "in", ["out_invoice", "out_refund", "in_invoice", "in_refund"]),
                ("activity_id", "=", self.activity_id.id),
            ],
            "context": {
                "search_default_out_invoice": 1,
            },
        }
