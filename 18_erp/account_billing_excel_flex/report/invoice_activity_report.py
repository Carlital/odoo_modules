from odoo import fields, models


class InvoiceActivityReport(models.AbstractModel):
    _name = "report.account_billing_excel_flex.report_invoice_activity"
    _description = "Reporte de facturas por actividad"

    def _get_report_values(self, docids, data=None):
        data = data or {}
        date_from = fields.Date.to_date(data.get("date_from"))
        date_to = fields.Date.to_date(data.get("date_to"))
        activity_id = data.get("activity_id")

        domain = [
            ("move_type", "in", ["out_invoice", "out_refund", "in_invoice", "in_refund"]),
            ("state", "=", "posted"),
            ("invoice_date", ">=", date_from),
            ("invoice_date", "<=", date_to),
        ]

        if activity_id:
            domain.append(("activity_id", "=", activity_id))
        elif self.env.user.invoice_activity_id:
            domain.append(("activity_id", "=", self.env.user.invoice_activity_id.id))

        moves = self.env["account.move"].search(domain, order="invoice_date asc, name asc")

        totals = {
            "count": len(moves),
            "amount_untaxed": sum(moves.mapped("amount_untaxed")),
            "amount_tax": sum(moves.mapped("amount_tax")),
            "amount_total": sum(moves.mapped("amount_total")),
        }

        selected_activity = self.env["billing.activity"].browse(activity_id) if activity_id else self.env.user.invoice_activity_id

        return {
            "doc_ids": moves.ids,
            "doc_model": "account.move",
            "docs": moves,
            "date_from": date_from,
            "date_to": date_to,
            "selected_activity": selected_activity,
            "totals": totals,
        }
