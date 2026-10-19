from odoo import models, fields, api, _
from odoo.exceptions import AccessError




SUB_TYPES = [
    ("portabilidad", "Portabilidad"),
    ("migracion", "Migración"),
    ("lineas_nuevas", "Líneas Nuevas"),
    ("absent", "Absent"),
]

class CrmCustomSubCampaign(models.Model):
    _name = "crm.custom.subcampaign"
    _description = "Subcampaña base"
    _order = "campaign_id, sequence, name"

    name = fields.Char(required=True)
    campaign_id = fields.Many2one("crm.custom.campaign", required=True, ondelete="cascade", string="Campaña")
    subtype = fields.Selection(selection=SUB_TYPES, required=True, string="Tipo Subcampaña")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)


class CrmCustomPlanTemplate(models.Model):
    _name = "crm.custom.plan.template"
    _description = "Plantilla de Plan base"
    _order = "subcampaign_id, name"

    name = fields.Char(required=True)
    subcampaign_id = fields.Many2one("crm.custom.subcampaign", required=True, ondelete="cascade", string="Subcampaña")
    is_global = fields.Boolean(default=False)
    active = fields.Boolean(default=True)


class CrmCustomPlanTemplateSection(models.Model):
    _name = "crm.custom.plan.template.section"
    _description = "Sección de plantilla base"
    _order = "template_id, sequence, name"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    template_id = fields.Many2one("crm.custom.plan.template", required=True, ondelete="cascade", string="Plantilla")


class CrmCustomPlanTemplateAttr(models.Model):
    _name = "crm.custom.plan.template.attr"
    _description = "Atributo de plantilla base"
    _order = "template_id, sequence, name"

    name = fields.Char(required=True)
    code = fields.Char()
    sequence = fields.Integer(default=10)
    data_type = fields.Char()
    template_id = fields.Many2one("crm.custom.plan.template", required=True, ondelete="cascade", string="Plantilla")
    section_id = fields.Many2one("crm.custom.plan.template.section", ondelete="restrict", string="Sección")


class CrmCustomPlan(models.Model):
    _name = "crm.custom.plan"
    _description = "Plan base"
    _order = "subcampaign_id, name"

    name = fields.Char(required=True)
    code = fields.Char()
    subcampaign_id = fields.Many2one("crm.custom.subcampaign", required=True, ondelete="cascade", string="Subcampaña")
    template_id = fields.Many2one("crm.custom.plan.template", string="Plantilla")
    active = fields.Boolean(default=True)


class CrmCustomPlanValue(models.Model):
    _name = "crm.custom.plan.value"
    _description = "Valor de atributo base"
    _order = "plan_id, attribute_id"

    plan_id = fields.Many2one("crm.custom.plan", required=True, ondelete="cascade", string="Plan")
    attribute_id = fields.Many2one("crm.custom.plan.template.attr", required=True, ondelete="restrict", string="Atributo")
    value_char = fields.Char()
    value_text = fields.Text()
    value_int = fields.Integer()
    value_float = fields.Float()
    value_bool = fields.Boolean()
    value_date = fields.Date()
    value_selection = fields.Char()


class CrmCustomCampaign(models.Model):
    _name = "crm.custom.campaign"
    _description = "Campaña CRM Personalizada"
    _order = "name"

    name = fields.Char(required=True)
    fecha_inicio = fields.Date()
    fecha_fin = fields.Date()
    descripcion = fields.Text()
    descuento = fields.Float()
    activo = fields.Boolean(default=True)

    def _has_campaign_manage_rights(self):
        return (
            self.env.user.has_group("crm_custom_lead.group_jefe_operaciones")
            or self.env.user.has_group("crm_custom_lead.group_gerente")
            or self.env.user.has_group("crm_custom_lead.group_supervisor")
        )

    def write(self, vals):
        if not (self.env.context.get("install_mode") or self.env.is_superuser()):
            if not self._has_campaign_manage_rights():
                raise AccessError(_("Solo Jefe de Operaciones, Supervisor o Gerente Comercial pueden modificar campañas."))
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        if not (self.env.context.get("install_mode") or self.env.is_superuser()):
            if not self._has_campaign_manage_rights():
                raise AccessError(_("Solo Jefe de Operaciones, Supervisor o Gerente Comercial pueden crear campañas."))
        return super().create(vals_list)

