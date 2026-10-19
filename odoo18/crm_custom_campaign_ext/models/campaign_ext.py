from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError


SUB_TYPES = [
    ("portabilidad", "Portabilidad"),
    ("migracion", "Migración"),
    ("lineas_nuevas", "Líneas Nuevas"),
    ("absent", "Absent"),
]


class CrmCustomSubCampaign(models.Model):
    _inherit = "crm.custom.subcampaign"
    _description = "Subcampaña de Campaña"
    _order = "campaign_id, sequence, name"

    name = fields.Char(required=True)
    campaign_id = fields.Many2one(
        "bc.campaign",
        required=True,
        ondelete="cascade",
        string="Campaña",
    )
    subtype = fields.Selection(selection=SUB_TYPES, required=True, string="Tipo Subcampaña")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    template_ids = fields.One2many(
        "bc.plan.template", "subcampaign_id", string="Plantillas"
    )
    plan_ids = fields.One2many(
        "bc.plan", "subcampaign_id", string="Planes"
    )

    _sql_constraints = [
        (
            "sub_unique",
            "unique(campaign_id, subtype)",
            "La subcampaña ya existe para esta campaña.",
        )
    ]

    @api.onchange("subtype", "campaign_id")
    def _onchange_name(self):
        for r in self:
            if r.subtype and r.campaign_id:
                r.name = f"{r.campaign_id.name} - {dict(SUB_TYPES).get(r.subtype)}"


    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'subtype' in fields_list and not res.get('subtype'):
            # valor por defecto cuando se crea desde UI o desde código si no se pasa subtype
            res['subtype'] = 'portabilidad'
        return res

    @api.model
    def create(self, vals):
        # asegurar subtype si la importación/XML no lo proporciona
        if not vals.get('subtype'):
            vals['subtype'] = 'portabilidad'
        return super().create(vals)


DATA_TYPES = [
    ("char", "Texto corto"),
    ("text", "Texto largo"),
    ("integer", "Entero"),
    ("float", "Decimal"),
    ("boolean", "Booleano"),
    ("date", "Fecha"),
    ("selection", "Selección"),
]


class CrmCustomPlanTemplate(models.Model):
    _name = "bc.plan.template"
    _inherit = "crm.custom.plan.template"
    _description = "Plantilla de Plan"
    _order = "subcampaign_id, name"

    name = fields.Char(required=True)
    bc_subcampaign_id = fields.Many2one(
        "bc.subcampaign", required=True, ondelete="cascade", string="Subcampaña", domain="[('campaign_id','=', bc_campaign_current_id)]"
    )
    is_global = fields.Boolean(string="Es Global", default=False, help="Indica si la plantilla es global para todas las subcampañas")
    active = fields.Boolean(default=True)
    attribute_ids = fields.One2many(
        "bc.plan.template.attr", "template_id", string="Atributos"
    )
    section_ids = fields.One2many(
        "bc.plan.template.section", "template_id", string="Secciones"
    )

    def action_generate_default_sections(self):
        """Generar secciones base por defecto"""
        for rec in self:
            if not rec.section_ids:
                self.env['bc.plan.template.section'].create([
                    {'template_id': rec.id, 'sequence': 10, 'name': '1. Información general'},
                    {'template_id': rec.id, 'sequence': 20, 'name': '2. Características'},
                    {'template_id': rec.id, 'sequence': 30, 'name': '3. Precios'},
                ])
        return True


class CrmCustomPlanTemplateSection(models.Model):
    _name = "bc.plan.template.section"
    _description = "Sección de Plantilla de Plan"
    _order = "template_id, sequence, name"

    name = fields.Char(required=True, string="Nombre")
    sequence = fields.Integer(default=10, string="Secuencia")
    template_id = fields.Many2one(
        "bc.plan.template", required=True, ondelete="cascade", string="Plantilla"
    )


class CrmCustomPlanTemplateAttr(models.Model):
    _name = "bc.plan.template.attr"
    _description = "Atributo de Plantilla de Plan"
    _order = "template_id, sequence, name"

    name = fields.Char(required=True, string="Etiqueta")
    code = fields.Char(string="Código", help="Identificador técnico opcional")
    sequence = fields.Integer(default=10)
    data_type = fields.Selection(DATA_TYPES, required=True, default="char", string="Tipo")
    required = fields.Boolean(string="Requerido")
    help = fields.Char(string="Ayuda")
    selection_options = fields.Text(
        string="Opciones (selection)",
        help="Lista de opciones separadas por coma, ej: Básico, Plus, Pro",
    )
    unit = fields.Char(string="Unidad", help="Ej: USD, GB, min")
    template_id = fields.Many2one(
        "bc.plan.template", required=True, ondelete="cascade", string="Plantilla"
    )
    section_id = fields.Many2one(
        "bc.plan.template.section", string="Sección", ondelete="restrict"
    )

    _sql_constraints = [
        (
            "attr_unique_code",
            "unique(template_id, code)",
            "El código del atributo debe ser único por plantilla.",
        )
    ]


class CrmCustomPlan(models.Model):
    _inherit = "crm.custom.plan"
    _description = "Plan de Subcampaña"
    _order = "subcampaign_id, name"

    name = fields.Char(required=True, string="Nombre del Plan")
    code = fields.Char(string="Código")
    subcampaign_id = fields.Many2one(
        "bc.subcampaign", required=True, ondelete="cascade", string="Subcampaña"
    )
    template_id = fields.Many2one(
        "bc.plan.template",
        required=True,
        domain="[('subcampaign_id','=',subcampaign_id)]",
    )
    value_ids = fields.One2many("bc.plan.value", "plan_id", string="Valores")
    active = fields.Boolean(default=True)

    def action_sync_template_values(self):
        """Sincroniza los valores del plan con los atributos de la plantilla"""
        for rec in self:
            if not rec.template_id:
                continue
            existing_attrs = rec.value_ids.mapped('attribute_id')
            for attr in rec.template_id.attribute_ids:
                if attr not in existing_attrs:
                    self.env['bc.plan.value'].create({
                        'plan_id': rec.id,
                        'attribute_id': attr.id,
                    })
        return True

    def _check_values_cover_template(self):
        for rec in self:
            if not rec.template_id:
                continue
            tmpl_attr_ids = set(rec.template_id.attribute_ids.ids)
            val_attr_ids = set(rec.value_ids.mapped("attribute_id").ids)
            missing = tmpl_attr_ids - val_attr_ids
            if missing:
                pass


class CrmCustomPlanValue(models.Model):
    _name = "bc.plan.value"
    _inherit = "crm.custom.plan.value"
    _description = "Valor de Atributo del Plan"
    _order = "plan_id, attribute_id"

    bc_plan_id = fields.Many2one(
        "bc.plan", required=True, ondelete="cascade", string="Plan", domain="[('subcampaign_id','=', bc_subcampaign_id)]"
    )
    attribute_id = fields.Many2one(
        "bc.plan.template.attr", required=True, ondelete="restrict", string="Atributo"
    )
    attr_type = fields.Selection(
        related="attribute_id.data_type", store=False, string="Tipo"
    )
    
    section_id = fields.Many2one(
        related='attribute_id.section_id',
        string='Sección',
        store=True,
        index=True,
    )

    value_char = fields.Char(string="Texto")
    value_text = fields.Text(string="Texto largo")
    value_int = fields.Integer(string="Entero")
    value_float = fields.Float(string="Decimal")
    value_bool = fields.Boolean(string="Booleano")
    value_date = fields.Date(string="Fecha")
    value_selection = fields.Char(string="Selección")

    value_display = fields.Char(
        string="Valor",
        compute="_compute_value_display",
        help="Representación amigable del valor",
    )

    unit_rel = fields.Char(related='attribute_id.unit', string='Unidad', readonly=True)
    
    value_input = fields.Char(
        string="Valor",
        compute="_compute_value_input",
        inverse="_inverse_value_input",
        help="Campo unificado para entrada de valores"
    )

    _sql_constraints = [
        (
            "unique_plan_attr",
            "unique(plan_id, attribute_id)",
            "El atributo ya tiene un valor para este plan.",
        )
    ]

    @api.depends("value_char", "value_text", "value_int", "value_float", "value_bool", "value_date", "value_selection", "attr_type")
    def _compute_value_input(self):
        for rec in self:
            if rec.attr_type == 'char':
                rec.value_input = rec.value_char or ''
            elif rec.attr_type == 'text':
                rec.value_input = rec.value_text or ''
            elif rec.attr_type == 'integer':
                rec.value_input = str(rec.value_int) if rec.value_int else ''
            elif rec.attr_type == 'float':
                rec.value_input = str(rec.value_float) if rec.value_float else ''
            elif rec.attr_type == 'boolean':
                rec.value_input = 'Sí' if rec.value_bool else 'No'
            elif rec.attr_type == 'date':
                rec.value_input = str(rec.value_date) if rec.value_date else ''
            elif rec.attr_type == 'selection':
                rec.value_input = rec.value_selection or ''
            else:
                rec.value_input = ''

    def _inverse_value_input(self):
        for rec in self:
            if rec.attr_type == 'char':
                rec.value_char = rec.value_input
            elif rec.attr_type == 'text':
                rec.value_text = rec.value_input
            elif rec.attr_type == 'integer':
                try:
                    rec.value_int = int(rec.value_input) if rec.value_input else 0
                except ValueError:
                    rec.value_int = 0
            elif rec.attr_type == 'float':
                try:
                    rec.value_float = float(rec.value_input) if rec.value_input else 0.0
                except ValueError:
                    rec.value_float = 0.0
            elif rec.attr_type == 'boolean':
                rec.value_bool = rec.value_input.lower() in ('sí', 'si', 'yes', 'true', '1')
            elif rec.attr_type == 'date':
                rec.value_date = rec.value_input if rec.value_input else False
            elif rec.attr_type == 'selection':
                rec.value_selection = rec.value_input

    @api.depends("value_char", "value_text", "value_int", "value_float", "value_bool", "value_date", "value_selection", "attribute_id.unit")
    def _compute_value_display(self):
        for rec in self:
            v = None
            if rec.attr_type == "char":
                v = rec.value_char
            elif rec.attr_type == "text":
                v = rec.value_text
            elif rec.attr_type == "integer":
                v = str(rec.value_int) if rec.value_int is not None else None
            elif rec.attr_type == "float":
                v = ("%g" % rec.value_float) if rec.value_float is not None else None
            elif rec.attr_type == "boolean":
                v = _("Sí") if rec.value_bool else _("No")
            elif rec.attr_type == "date":
                v = rec.value_date and fields.Date.to_string(rec.value_date)
            elif rec.attr_type == "selection":
                v = rec.value_selection
            if v and rec.attribute_id.unit:
                rec.value_display = f"{v} {rec.attribute_id.unit}"
            else:
                rec.value_display = v or ""

    @api.onchange("attribute_id")
    def _onchange_attribute_id(self):
        for rec in self:
            rec.value_char = False
            rec.value_text = False
            rec.value_int = False
            rec.value_float = False
            rec.value_bool = False
            rec.value_date = False
            rec.value_selection = False


class CrmLead(models.Model):
    _inherit = "crm.lead"

    subcampaign_id = fields.Many2one(
        "bc.subcampaign",
        string="Subcampaña",
        domain="[('campaign_id','=', bc_campaign_current_id)]",
    )
    plan_id = fields.Many2one(
        "bc.plan", string="Plan", domain="[('subcampaign_id','=',subcampaign_id)]"
    )


class CrmCustomCampaign(models.Model):
    _inherit = "crm.custom.campaign"
    subcampaign_ids = fields.One2many(
        "bc.subcampaign", "campaign_id", string="Subcampañas"
    )
