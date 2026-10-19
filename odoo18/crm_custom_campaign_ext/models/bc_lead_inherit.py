from odoo import api, fields, models, _
from datetime import date

class CrmLead(models.Model):
    _inherit = "crm.lead"
    bc_campaign_current_id = fields.Many2one(
        "bc.campaign", string="Campaña vigente",
        compute="_compute_bc_campaign_current_id", store=False, readonly=True
    )
    bc_subcampaign_id = fields.Many2one(
        "bc.subcampaign", string="Subcampaña",
        domain="[('campaign_id','=', bc_campaign_current_id), ('active','=', True)]"
    )
    bc_plan_id = fields.Many2one(
        "bc.plan", string="Plan",
        domain="[('subcampaign_id','=', bc_subcampaign_id), ('active','=', True)]"
    )
    bc_oferta_resumen = fields.Text(string="Oferta (resumen)", readonly=True)
    bc_oferta_guion = fields.Text(string="Guion Comercial", readonly=True)

    @api.depends("custom_campaign_id")
    def _compute_bc_campaign_current_id(self):
        Campaign = self.env["bc.campaign"]
        current = Campaign.get_current_campaign()
        for rec in self:
            # valor por defecto: la campaña "current" (si existe)
            value = current.id if current else False
            # si custom_campaign_id está presente, intentar obtener un id compatible
            if rec.custom_campaign_id:
                try:
                    # si es del mismo modelo bc.campaign, usarlo directamente
                    if getattr(rec.custom_campaign_id, "_name", "") == "bc.campaign":
                        value = rec.custom_campaign_id.id or value
                    # si el custom campaign referencia una bc.campaign en un campo típico
                    elif hasattr(rec.custom_campaign_id, "campaign_id"):
                        value = rec.custom_campaign_id.campaign_id.id or value
                    elif hasattr(rec.custom_campaign_id, "bc_campaign_id"):
                        value = rec.custom_campaign_id.bc_campaign_id.id or value
                    # en otros casos no usar el id (evita asignar id de otro modelo)
                except Exception:
                    value = value
            rec.bc_campaign_current_id = value

    @api.onchange("bc_plan_id")
    def _onchange_bc_plan_id_generate_snapshots(self):
        for rec in self:
            resumen = ""
            guion = ""
            plan = rec.bc_plan_id
            if plan:
                header_parts = [f"Plan {plan.name}"]
                if plan.price_with_tax:
                    sym = plan.currency_id and plan.currency_id.symbol or ""
                    header_parts.append(f"{plan.price_with_tax:.2f} {sym} con IVA")
                header = " - ".join(header_parts)
                if plan.headline:
                    header = f"{header} | {plan.headline}"

                lines = plan.line_ids.filtered(lambda l: l.active).sorted(lambda l: (l.sequence, l.id))
                bullets = []
                for ln in lines:
                    title = ln.titulo or ""
                    det = f" ({ln.detalle})" if ln.detalle else ""
                    bullets.append(f"• {title}{det}")
                resumen = header + ("\n" + "\n".join(bullets) if bullets else "")

                dialog_lines = [f"Estimado cliente, le ofrezco el {plan.name}."]
                if plan.headline:
                    dialog_lines.append(f"Resumen: {plan.headline}.")
                if plan.price_with_tax:
                    sym = plan.currency_id and plan.currency_id.symbol or ""
                    dialog_lines.append(f"El precio final es {plan.price_with_tax:.2f} {sym} con IVA.")
                if lines:
                    dialog_lines.append("Incluye:")
                    for ln in lines:
                        det = f": {ln.detalle}" if ln.detalle else ""
                        dialog_lines.append(f"- {ln.titulo}{det}.")
                guion = "\n".join(dialog_lines)

            rec.bc_oferta_resumen = resumen
            rec.bc_oferta_guion = guion
