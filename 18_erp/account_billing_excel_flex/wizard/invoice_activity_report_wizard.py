from odoo import _, fields, models
from odoo.exceptions import UserError


class InvoiceActivityReportWizard(models.TransientModel):
    _name = "invoice.activity.report.wizard"
    _description = "Wizard reporte de facturas por actividad"

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    activity_id = fields.Many2one(
        "billing.activity",
        string="Actividad",
        domain="[('id', 'in', user_activity_ids)]",
    )
    user_activity_ids = fields.Many2many(
        "billing.activity",
        compute="_compute_user_activity_ids",
    )

    def _compute_user_activity_ids(self):
        for wizard in self:
            wizard.user_activity_ids = self.env.user.billing_activity_ids

    def action_print_report(self):
        self.ensure_one()
        if self.date_from > self.date_to:
            raise UserError(_("La fecha inicial no puede ser mayor que la fecha final."))

        data = {
            "date_from": str(self.date_from),
            "date_to": str(self.date_to),
            "activity_id": self.activity_id.id or False,
        }
        return self.env.ref("account_billing_excel_flex.action_report_invoice_activity").report_action(self, data=data)
