from datetime import date
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
import base64
import logging
import psycopg2
_logger = logging.getLogger(__name__)

class BcCampaign(models.Model):
    _name = "bc.campaign"
    _inherit = "crm.custom.campaign"
    _description = "Campaña Comercial (BC)"
    _order = "date_start desc, name"

    name = fields.Char(required=True)
    date_start = fields.Date(required=True)
    date_end = fields.Date(required=True)
    active = fields.Boolean(default=True)

    subcampaign_ids = fields.One2many(
        "bc.subcampaign",
        "campaign_id",
        string="Subcampañas",
    )

    # ---- security helpers ----
    def _has_manage_rights(self):
        user = self.env.user
        return (
            user.has_group("base.group_system")
            or user.has_group("crm_custom_lead.group_jefe_operaciones")
        )

    def write(self, vals):
        if not (self.env.context.get("install_mode") or self.env.is_superuser()):
            if not self._has_manage_rights():
                raise AccessError(
                    _("Solo Administrador y Jefe de Operaciones pueden modificar campañas.")
                )
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        if not (self.env.context.get("install_mode") or self.env.is_superuser()):
            if not self._has_manage_rights():
                raise AccessError(
                    _("Solo Administrador y Jefe de Operaciones pueden crear campañas.")
                )
        return super(BcCampaign, self).create(vals_list)

    def unlink(self):
        if not (self.env.context.get("install_mode") or self.env.is_superuser()):
            if not self._has_manage_rights():
                raise AccessError(
                    _("Solo Administrador y Jefe de Operaciones pueden eliminar campañas.")
                )
        return super().unlink()

    @api.model
    def get_current_campaign(self):
        today = date.today()
        return self.search(
            [
                ("active", "=", True),
                ("date_start", "<=", today),
                ("date_end", ">=", today),
            ],
            limit=1,
        )


class BcSubcampaign(models.Model):
    _name = "bc.subcampaign"
    _inherit = "crm.custom.subcampaign"
    _description = "Subcampaña Comercial (BC)"
    _order = "campaign_id, name"

    name = fields.Char(required=True)
    campaign_id = fields.Many2one(
        "bc.campaign",
        required=True,
        ondelete="cascade",
        string="Campaña",
    )
    note = fields.Text(string="Nota")
    active = fields.Boolean(default=True)

    plan_ids = fields.One2many(
        "bc.plan",
        "subcampaign_id",
        string="Planes",
    )

    # Agregado: HTML computed para la vista comercial (tarjetas con miniaturas)
    bc_gallery_html = fields.Html(
        string="Vista comercial (HTML)",
        compute="_compute_bc_gallery_html",
        sanitize=False,
        readonly=True,
    )

    # DEBUG: lista de nombres de iconos detectados en la subcampaña (útil para diagnosticar)
    bc_gallery_debug_names = fields.Char(
        string='Debug: Iconos detectados',
        compute='_compute_bc_gallery_debug_names',
        read_only=True,
    )

    @api.depends(
        "plan_ids",
        "plan_ids.active",
        "plan_ids.line_ids",
        "plan_ids.line_ids.titulo",
        "plan_ids.line_ids.icon_ids",
        "plan_ids.line_ids.icon_ids.image_128",
        "plan_ids.line_ids.icon_ids.image",
    )
    def _compute_bc_gallery_html(self):
        def looks_like_b64(s):
            try:
                if not s or not isinstance(s, str):
                    return False
                import re
                if not re.fullmatch(r"[A-Za-z0-9+/=\n\r]+", s):
                    return False
                return (len(s.replace("\n", "").replace("\r", "")) % 4) == 0
            except Exception:
                return False

        def to_b64(img):
            if not img:
                return None
            if isinstance(img, str):
                return img if looks_like_b64(img) else None
            try:
                if isinstance(img, (bytes, bytearray, memoryview)):
                    try:
                        txt = bytes(img).decode("utf-8")
                        return txt if looks_like_b64(txt) else base64.b64encode(bytes(img)).decode()
                    except Exception:
                        return base64.b64encode(bytes(img)).decode()
                b = bytes(img)
                return base64.b64encode(b).decode()
            except Exception:
                return None

        for rec in self:
            parts = []
            plans = rec.plan_ids.filtered(lambda p: p.active)
            for plan in plans:
                lines_html = []
                for ln in plan.line_ids:
                    text = ln.titulo or ""
                    if ln.detalle:
                        text = f"{text}<div style='font-size:11px;color:#bdbdbd'>{ln.detalle}</div>"

                    icon_imgs = []
                    for icon in ln.icon_ids:
                        img_data = icon.image_128 or icon.image
                        if isinstance(img_data, str) and img_data.startswith("b'") and img_data.endswith("'"):
                            try:
                                img_data = img_data[2:-1]
                            except Exception:
                                pass
                        b64 = to_b64(img_data)
                        mimetype = (icon.mimetype or "").strip() or "image/png"
                        if b64 and isinstance(b64, str) and len(b64) > 16:
                            src = f"data:{mimetype};base64,{b64}"
                            icon_imgs.append(
                                f"<img src='{src}' style='height:20px;margin-left:6px;vertical-align:middle;border-radius:3px' alt='{(icon.name or '')}'/>"
                            )
                    icons_inline = ""
                    if icon_imgs:
                        icons_inline = f"<div style='margin-top:6px'>{''.join(icon_imgs)}</div>"

                    lines_html.append(
                        f"<div style='margin-bottom:6px;padding:8px;background:rgba(0,0,0,0.12);border-radius:4px;color:#fff'>"
                        f"{text}"
                        f"{icons_inline}"
                        f"</div>"
                    )

                price_html = ""
                try:
                    if plan.price_with_tax:
                        currency = plan.currency_id and plan.currency_id.symbol or ""
                        price_html = f"<div style='font-weight:700;color:#fff;margin-top:8px'>{plan.price_with_tax} {currency} Incl. IVA</div>"
                except Exception:
                    price_html = ""

                card = f"""
                <div style='background:#263238;color:#fff;border-radius:8px;padding:14px;width:300px;margin:8px;display:inline-block;vertical-align:top;box-shadow:0 8px 16px rgba(0,0,0,0.25)'>
                    <div style='font-size:14px;font-weight:700;text-transform:uppercase;margin-bottom:8px'>{plan.name}</div>
                    <div style='color:#bdbdbd;font-size:12px;margin-bottom:8px'>{plan.headline or ''}</div>
                    <div style='margin-bottom:8px'>{''.join(lines_html)}</div>
                    {price_html}
                </div>
                """
                parts.append(card)
            rec.bc_gallery_html = "<div style='display:flex;flex-wrap:wrap;gap:8px'>" + "".join(parts) + "</div>"

    @api.depends('plan_ids', 'plan_ids.line_ids.icon_ids')
    def _compute_bc_gallery_debug_names(self):
        for rec in self:
            names = rec.plan_ids.mapped('line_ids.icon_ids.name')
            rec.bc_gallery_debug_names = ', '.join(filter(None, map(str, names))) or ''

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        sub_id = self.env.context.get('default_subcampaign_id')
        if sub_id:
            res.setdefault('subcampaign_id', sub_id)
        return res

    def action_open_gsheet_import_wizard(self):
        self.ensure_one()
        action = {
            "type": "ir.actions.act_window",
            "res_model": "bc.gsheet.import.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_subcampaign_id": self.id},
        }
        return action


class BcPlan(models.Model):
    _name = "bc.plan"
    _inherit = "crm.custom.plan"
    _description = "Plan Comercial (BC)"
    _order = "subcampaign_id, sequence, name"

    name = fields.Char(required=True)
    subcampaign_id = fields.Many2one(
        "bc.subcampaign",
        required=True,
        ondelete="cascade",
        string="Subcampaña",
    )
    sequence = fields.Integer(default=10)

    price_no_tax = fields.Monetary(string="Precio sin IVA")
    price_with_tax = fields.Monetary(string="Precio con IVA")
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )

    headline = fields.Char(string="Resumen")

    line_ids = fields.One2many(
        "bc.plan.line",
        "plan_id",
        string="Bloques",
        copy=True,
    )

    active = fields.Boolean(default=True)


    @api.model_create_multi
    def create(self, vals_list):
        field = self._fields.get("template_id")
        if not field:
            return super(BcPlan, self).create(vals_list)

        comodel = getattr(field, "comodel_name", None)
        TemplateModel = self.env[comodel] if comodel else None

        for vals in vals_list:
            if vals.get("template_id"):
                continue

            template_rec = None

            try:
                if TemplateModel:
                    template_rec = TemplateModel.search([("is_global", "=", True)], limit=1)
            except Exception:
                template_rec = None

            if not template_rec and TemplateModel and vals.get("subcampaign_id"):
                try:
                    if "bc_subcampaign_id" in TemplateModel._fields:
                        template_rec = TemplateModel.search([("bc_subcampaign_id", "=", vals.get("subcampaign_id"))], limit=1)
                except Exception:
                    template_rec = None
                if not template_rec:
                    try:
                        template_rec = TemplateModel.search([("subcampaign_id", "=", vals.get("subcampaign_id"))], limit=1)
                    except Exception:
                        template_rec = None

            if not template_rec and TemplateModel:
                try:
                    template_rec = TemplateModel.search([], limit=1)
                except Exception:
                    template_rec = None

            if not template_rec:
                try:
                    tpl_ref = self.env.ref('crm_custom_campaign_ext.plan_template_base', raise_if_not_found=False)
                    if tpl_ref:
                        template_rec = tpl_ref
                except Exception:
                    template_rec = template_rec

            if not template_rec and TemplateModel:
                create_vals = {}
                if "bc_subcampaign_id" in TemplateModel._fields and vals.get("subcampaign_id"):
                    create_vals["bc_subcampaign_id"] = vals.get("subcampaign_id")
                if "subcampaign_id" in TemplateModel._fields and vals.get("subcampaign_id"):
                    create_vals["subcampaign_id"] = vals.get("subcampaign_id")
                if "name" in TemplateModel._fields:
                    create_vals.setdefault("name", "default_template")
                if "is_global" in TemplateModel._fields:
                    create_vals.setdefault("is_global", True)
                try:
                    template_rec = TemplateModel.create(create_vals)
                except Exception as e:
                    template_rec = None

            if template_rec:
                vals["template_id"] = template_rec.id
            else:
                required_fields = []
                try:
                    if TemplateModel:
                        required_fields = [n for n, f in TemplateModel._fields.items() if getattr(f, "required", False)]
                except Exception:
                    required_fields = []
                msg = (
                    "No se proporcionó 'template_id' al crear bc.plan y no se encontró ni pudo crearse un "
                    "template por defecto.\n\nProporciona 'template_id' en los datos de importación o crea "
                    "una plantilla por defecto en el módulo (data XML) con los campos requeridos."
                )
                if required_fields:
                    msg += f"\n\nCampos requeridos detectados en el modelo de plantilla: {', '.join(required_fields)}"
                raise UserError(msg)

        return super(BcPlan, self).create(vals_list)


class BcPlanLine(models.Model):
    _name = "bc.plan.line"
    _description = "Bloque del Plan Comercial (BC)"
    _order = "plan_id, sequence, id"

    plan_id = fields.Many2one(
        "bc.plan",
        required=True,
        ondelete="cascade",
        string="Plan",
    )
    sequence = fields.Integer(default=10)

    titulo = fields.Char(required=True, string="Título")
    detalle = fields.Char(string="Detalle")

    tipo = fields.Selection(
        [
            ("gb", "GB/Datos"),
            ("min", "Minutos"),
            ("roaming", "Roaming"),
            ("beneficio", "Beneficio"),
            ("precio", "Precio"),
            ("otro", "Otro"),
        ],
        default="otro",
        string="Tipo",
    )

    icon_hint = fields.Char(string="Icon Hint / Pista")
    icon_ids = fields.Many2many(
        "bc.icon",
        "bc_plan_line_icon_rel",
        "line_id",
        "icon_id",
        string="Iconos",
    )
    mimetype = fields.Char(string="MIME Type")
    active = fields.Boolean(default=True)


class BcIcon(models.Model):
    _name = 'bc.icon'
    _description = 'Icono / recurso multimedia para líneas de plan'
    _order = 'sequence, name'

    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Nombre', required=True)
    image = fields.Binary(string='Imagen/Icono')
    image_128 = fields.Binary(string='Imagen 128')
    mimetype = fields.Char(string='MIME Type')
    active = fields.Boolean(string='Active', default=True)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    custom_campaign_id = fields.Many2one(
        'crm.custom.campaign',
        string='Campaña (CRM Custom)',
    )

    bc_campaign_id = fields.Many2one(
        'bc.campaign',
        string='Campaña (BC)',
        compute='_compute_bc_campaign_id',
        inverse='_inverse_bc_campaign_id',
        store=False,
    )

    @api.depends('custom_campaign_id')
    def _compute_bc_campaign_id(self):
        for rec in self:
            rec.bc_campaign_id = False
            c = rec.custom_campaign_id
            if c:
                bc = self.env['bc.campaign'].search([('name', '=', c.name)], limit=1)
                if bc:
                    rec.bc_campaign_id = bc

    def _inverse_bc_campaign_id(self):
        for rec in self:
            bc = rec.bc_campaign_id
            if not bc:
                rec.custom_campaign_id = False
                continue
            c = self.env['crm.custom.campaign'].search([('name', '=', bc.name)], limit=1)
            if c:
                rec.custom_campaign_id = c
            else:
                try:
                    c = self.env['crm.custom.campaign'].create({'name': bc.name})
                    rec.custom_campaign_id = c
                except Exception:
                    rec.custom_campaign_id = rec.custom_campaign_id

    bc_subcampaign_id = fields.Many2one(
        'bc.subcampaign',
        string='Subcampaña (BC)',
        compute='_compute_bc_subcampaign_id',
        inverse='_inverse_bc_subcampaign_id',
        store=False,
    )

    @api.depends('bc_campaign_id')
    def _compute_bc_subcampaign_id(self):
        for rec in self:
            rec.bc_subcampaign_id = False
            custom_sub = getattr(rec, 'custom_subcampaign_id', False)
            if custom_sub:
                domain = [('name', '=', custom_sub.name)]
                if rec.bc_campaign_id:
                    domain.append(('campaign_id', '=', rec.bc_campaign_id.id))
                bc_sub = self.env['bc.subcampaign'].search(domain, limit=1)
                if bc_sub:
                    rec.bc_subcampaign_id = bc_sub
                    continue
            if rec.bc_campaign_id:
                subs = self.env['bc.subcampaign'].search([('campaign_id', '=', rec.bc_campaign_id.id), ('active', '=', True)])
                if len(subs) == 1:
                    rec.bc_subcampaign_id = subs[0]

    def _inverse_bc_subcampaign_id(self):
        for rec in self:
            bc_sub = rec.bc_subcampaign_id
            if not bc_sub:
                try:
                    rec.custom_subcampaign_id = False
                except Exception:
                    pass
                continue
            CustomSub = self.env['crm.custom.subcampaign']
            # preferir búsqueda por (name, campaign_id, subtype) para evitar violar unique constraint
            domain = [('name', '=', bc_sub.name)]
            if bc_sub.campaign_id:
                domain.append(('campaign_id', '=', bc_sub.campaign_id.id))
            if getattr(bc_sub, 'subtype', False):
                domain.append(('subtype', '=', bc_sub.subtype))

            try:
                # usar sudo para evitar problemas de permisos en hooks/onchange desde UI/web
                c = CustomSub.sudo().search(domain, limit=1)
                if c:
                    rec.custom_subcampaign_id = c
                    continue

                # Asegurar campaign custom (reutilizar o crear)
                CustomCampaign = self.env['crm.custom.campaign']
                campaign_name = bc_sub.campaign_id and bc_sub.campaign_id.name or False
                campaign_rec = None
                if campaign_name:
                    campaign_rec = CustomCampaign.sudo().search([('name', '=', campaign_name)], limit=1)
                if not campaign_rec and campaign_name:
                    try:
                        campaign_rec = CustomCampaign.sudo().create({'name': campaign_name})
                    except Exception:
                        campaign_rec = None

                create_vals = {'name': bc_sub.name}
                if campaign_rec:
                    create_vals['campaign_id'] = campaign_rec.id
                if getattr(bc_sub, 'subtype', False):
                    create_vals['subtype'] = bc_sub.subtype

                try:
                    c = CustomSub.sudo().create(create_vals)
                except (psycopg2.errors.UniqueViolation, psycopg2.IntegrityError) as e:
                    # Posible race: otro proceso creó el registro simultáneamente.
                    # Hacer rollback del cursor y re-buscar el registro existente.
                    logging.getLogger(__name__).warning('Creación crm.custom.subcampaign race condition: %s. Haciendo rollback y re-buscando.', e)
                    try:
                        # rollback to clear failed statement and allow subsequent queries
                        self.env.cr.rollback()
                    except Exception:
                        pass
                    c = CustomSub.sudo().search(domain, limit=1)
                except Exception:
                    logging.getLogger(__name__).exception('Creación crm.custom.subcampaign falló inesperadamente')
                    c = CustomSub.sudo().search(domain, limit=1)

                if c:
                    rec.custom_subcampaign_id = c
            except Exception:
                # no dejar que un fallo aquí aborte la transacción completa
                logging.getLogger(__name__).exception('Error en _inverse_bc_subcampaign_id (ignorado)')
                pass

    bc_plan_icons_html = fields.Html(
        string='Iconos del Plan (vista)',
        compute='_compute_bc_plan_icons_html',
        sanitize=False,
        readonly=True,
    )

    bc_plan_icon_ids = fields.Many2many(
        'bc.icon',
        'crm_lead_bc_icon_rel',
        'lead_id',
        'icon_id',
        string='Iconos del Plan (compat)',
        compute='_compute_bc_plan_icon_ids',
        store=False,
        readonly=True,
    )

    bc_debug_icon_names = fields.Char(
        string='Debug: Iconos del Plan',
        compute='_compute_bc_debug_icon_names',
        read_only=True,
    )

    @api.depends('bc_plan_id')
    def _compute_bc_plan_icon_ids(self):
        for rec in self:
            if getattr(rec, 'bc_plan_id', False):
                icon_ids = rec.bc_plan_id.line_ids.mapped('icon_ids').ids
                rec.bc_plan_icon_ids = [(6, 0, icon_ids)]
            else:
                rec.bc_plan_icon_ids = [(5,)]

    @api.depends('bc_plan_id')
    def _compute_bc_plan_icons_html(self):
        def to_b64(img):
            if not img:
                return None
            if isinstance(img, str):
                return img
            try:
                b = bytes(img)
                return base64.b64encode(b).decode()
            except Exception:
                return None

        for rec in self:
            html_fragments = []
            plan = getattr(rec, 'bc_plan_id', False)
            if plan:
                icons = plan.line_ids.mapped('icon_ids')
                for icon in icons:
                    img_data = icon.image_128 or icon.image
                    if isinstance(img_data, str) and img_data.startswith("b'") and img_data.endswith("'"):
                        try:
                            img_data = img_data[2:-1]
                        except Exception:
                            pass
                    b64 = to_b64(img_data)
                    mimetype = (icon.mimetype or "").strip() or 'image/png'
                    if b64 and isinstance(b64, str) and len(b64) > 16:
                        src = f"data:{mimetype};base64,{b64}"
                        html_fragments.append(f"<img src='{src}' style='height:32px; margin-right:6px; vertical-align:middle;' alt='{(icon.name or '')}'/>")
                    else:
                        html_fragments.append(f"<span style='display:inline-block; margin-right:6px; padding:2px 6px; background:#f3f3f3; border-radius:4px;'>{(icon.name or '')}</span>")
            rec.bc_plan_icons_html = "".join(html_fragments)

    @api.depends('bc_plan_id')
    def _compute_bc_debug_icon_names(self):
        for rec in self:
            if getattr(rec, 'bc_plan_id', False):
                names = rec.bc_plan_id.line_ids.mapped('icon_ids.name')
                rec.bc_debug_icon_names = ', '.join(filter(None, map(str, names)))
            else:
                rec.bc_debug_icon_names = ''

    bc_oferta_resumen_html = fields.Html(
        string='Oferta (Resumen HTML)',
        compute='_compute_bc_oferta_resumen_html',
        sanitize=False,
        readonly=True,
    )

    @api.depends(
        'bc_plan_id',
        'bc_plan_id.value_ids',
        'bc_plan_id.value_ids.value_char',
        'bc_plan_id.value_ids.value_text',
        'bc_plan_id.value_ids.value_bool',
        'bc_plan_id.value_ids.value_float',
        'bc_plan_id.template_id',
        'bc_plan_id.template_id.attribute_ids',
        'bc_plan_id.template_id.attribute_ids.name',
        'bc_plan_id.line_ids',
        'bc_plan_id.line_ids.titulo',
        'bc_plan_id.line_ids.detalle',
    )
    def _compute_bc_oferta_resumen_html(self):
        for rec in self:
            plan = getattr(rec, 'bc_plan_id', False)
            if not plan:
                rec.bc_oferta_resumen_html = ''
                continue

            currency = plan.currency_id and plan.currency_id.symbol or ''
            price_html = ''
            try:
                if plan.price_with_tax:
                    price_html = f"<div style='font-weight:700;color:#263238;margin-top:6px'>{plan.price_with_tax:.2f} {currency} (IVA incluido)</div>"
            except Exception:
                price_html = ''

            lines = plan.line_ids.filtered(lambda l: l.active) if getattr(plan, 'line_ids', False) else []
            if lines:
                items = []
                for ln in lines:
                    det = f": {ln.detalle}" if ln.detalle else ""
                    items.append(f"<li style='margin-bottom:6px;'><strong>{(ln.titulo or '')}</strong>{det}</li>")
                lines_html = f"<ul style='padding-left:18px;margin-top:8px;color:#333'>{''.join(items)}</ul>"
            else:
                lines_html = "<div style='color:#999;margin-top:8px'>(Sin bloques definidos)</div>"

            attrs_html = ""
            try:
                if getattr(plan, 'value_ids', False):
                    attrs_present = plan.value_ids.mapped('attribute_id')
                else:
                    attrs_present = []
            except Exception:
                attrs_present = []

            if attrs_present:
                rows = []
                for attr in attrs_present:
                    pa = plan.value_ids.filtered(lambda v, a=attr: getattr(v, 'attribute_id', False) and v.attribute_id.id == a.id)
                    if pa:
                        try:
                            val = pa[0].get_display_value()
                        except Exception:
                            try:
                               val = pa[0].value_char or pa[0].value_text or ('S' if getattr(pa[0], 'value_bool', None) else 'N') or (str(pa[0].value_float) if getattr(pa[0], 'value_float', None) not in (None, '') else 'S/N')
                            except Exception:
                                val = 'S/N'
                    else:
                        val = 'S/N'
                    rows.append(f"<tr><td style='padding:6px 8px;font-weight:600'>{attr.name}</td><td style='padding:6px 8px'>{val}</td></tr>")
                attrs_html = f"<table style='width:100%;border-collapse:collapse;margin-top:8px'>{''.join(rows)}</table>"



            card = f"""
            <div style='border:1px solid #e6e6e6;border-radius:8px;padding:12px;background:#fff;max-width:560px;box-shadow:0 2px 6px rgba(0,0,0,0.03)'>
                <div style='display:flex;justify-content:space-between;align-items:flex-start;'>
                    <div>
                        <div style='font-weight:700;font-size:15px;text-transform:uppercase;color:#222'>{(plan.name or '')}</div>
                        <div style='color:#666;font-size:13px;margin-top:4px'>{(plan.headline or '')}</div>
                    </div>
                    <div style='text-align:right;min-width:120px'>
                        {price_html}
                    </div>
                </div>
                {lines_html}
                {attrs_html}
            </div>
            """
            rec.bc_oferta_resumen_html = card