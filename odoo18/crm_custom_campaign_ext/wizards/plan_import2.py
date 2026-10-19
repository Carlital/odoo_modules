import base64
import io
import re
import unicodedata

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CampaignPlanImportWizard(models.TransientModel):
    _name = "bc.plan.import.wizard"
    _description = "Importar plantillas y planes desde XLSX"

    campaign_id = fields.Many2one("bc.campaign", string="Campana")
    subcampaign_id = fields.Many2one(
        "bc.subcampaign",
        string="Subcampana",
        domain="[('campaign_id','=',campaign_id)]",
        required=False,
    )
    xlsx_file = fields.Binary(string="Archivo XLSX", required=True)
    filename = fields.Char(string="Nombre del archivo")
    sheet_name = fields.Char(string="Hoja (opcional)")
    create_template = fields.Boolean(string="Crear plantilla", default=True)
    template_name = fields.Char(string="Nombre plantilla")
    create_plans = fields.Boolean(string="Crear planes", default=True)
    header_row = fields.Integer(string="Fila de encabezados", default=3,
                                help="Fila (1-based) donde estan los nombres de los atributos, p. ej. 3")
    plan_header = fields.Char(string="Etiqueta columna Plan", default="PLAN",
                              help="Nombre exacto del encabezado con el nombre del plan; si se omite, se usa la primera columna.")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        if active_model == 'bc.campaign' and active_id:
            res.setdefault('campaign_id', active_id)
        if active_model == 'bc.subcampaign' and active_id:
            sub = self.env['bc.subcampaign'].browse(active_id)
            if sub.exists():
                res.setdefault('campaign_id', sub.campaign_id.id)
                res.setdefault('subcampaign_id', sub.id)
        return res

    def _read_xlsx(self):
        try:
            import pandas as pd
        except Exception:
            raise UserError(_("Pandas no esta instalado en el servidor."))

        if not self.xlsx_file:
            raise UserError(_("Suba un archivo XLSX."))
        data = base64.b64decode(self.xlsx_file)
        bio = io.BytesIO(data)
        try:
            xls = pd.read_excel(bio, sheet_name=None, dtype=object, engine="openpyxl")
        except Exception as e:
            raise UserError(_("No se pudo leer el XLSX: %s") % e)
        non_empty = {n: df for n, df in xls.items() if not df.empty and len(df.columns) > 0}
        if not non_empty:
            raise UserError(_("El archivo no contiene hojas con datos."))
        if self.sheet_name and self.sheet_name in non_empty:
            return self.sheet_name, non_empty[self.sheet_name]
        prio = ["GUIA", "PLAN", "MIGR", "DIGITAL", "TRADIC", "PORTAB", "UPSELL"]
        def score(name):
            up = name.upper()
            return sum(k in up for k in prio), -len(non_empty[name])
        sheet = sorted(non_empty.keys(), key=score, reverse=True)[0]
        return sheet, non_empty[sheet]

    def _is_numericish(self, s):
        return bool(re.match(r'^[\s\d.,%]+$', str(s or '').strip()))

    def _build_from_header_row(self, df):
        import pandas as pd
        hr = max(1, int(self.header_row or 1)) - 1
        if hr >= len(df):
            hr = 0

        def build(idx):
            header_series = df.iloc[idx:idx+1].fillna("").astype(str).iloc[0]
            headers = []
            for i, val in enumerate(header_series.tolist()):
                name = (val or "").strip()
                if not name or name.lower().startswith("unnamed"):
                    name = f"Col {i+1}"
                headers.append(name)
            data_df = df.iloc[idx+1:].reset_index(drop=True)
            data_df.columns = headers
            return headers, data_df

        headers, data_df = build(hr)

        numeric_ratio = sum(1 for h in headers if self._is_numericish(h)) / max(len(headers), 1)
        if numeric_ratio >= 0.6 and hr > 0:
            headers, data_df = build(hr - 1)

        label = (self.plan_header or "").strip().upper()
        if label and label not in [str(h).strip().upper() for h in headers]:
            for cand in range(0, min(6, len(df))):
                row_vals = [str(v).strip().upper() for v in df.iloc[cand:cand+1].fillna("").astype(str).iloc[0].tolist()]
                if label in row_vals:
                    headers, data_df = build(cand)
                    break
        return headers, data_df

    def _infer_type(self, series):
        import pandas as pd
        s = series.dropna()
        if s.empty:
            return "char"
        try:
            num = pd.to_numeric(s.astype(str).str.replace(",", "", regex=False), errors="coerce")
            if num.notna().mean() >= 0.95:
                return "float"
        except Exception:
            pass
        lows = s.astype(str).str.strip().str.lower()
        if lows.isin(["si", "no", "true", "false", "1", "0", "y", "n"]).mean() >= 0.8:
            return "boolean"
        if lows.str.len().mean() > 100:
            return "text"
        return "char"

    def _slug(self, text):
        txt = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode("ascii")
        txt = re.sub(r"[^a-zA-Z0-9_\- ]+", "", txt)
        txt = re.sub(r"[\s\-]+", "_", txt).strip("_").lower()
        return txt

    def action_import(self):
        self.ensure_one()
        if not self.subcampaign_id:
            raise UserError(_("Seleccione una subcampana para continuar."))
        sheet_name, df = self._read_xlsx()
        headers, df = self._build_from_header_row(df)
        name_col = headers[0]
        label = (self.plan_header or "").strip().upper()
        if label:
            for h in headers:
                if str(h).strip().upper() == label:
                    name_col = h
                    break
        template = None
        if self.create_template:
            tname = self.template_name or f"{self.subcampaign_id.name} - {sheet_name}"
            template = self.env["bc.plan.template"].create({
                "name": tname,
                "subcampaign_id": self.subcampaign_id.id,
            })
            Attr = self.env["bc.plan.template.attr"]
            for j, h in enumerate(headers):
                if h == name_col:
                    continue
                name = str(h).strip()[:128]
                base_code = self._slug(name)
                code = base_code[:64] if base_code else False
                existing = Attr.search([
                    ("template_id", "=", template.id),
                    "|", ("name", "=", name), ("code", "=", code)
                ], limit=1)
                if existing:
                    continue
                used_codes = set(Attr.search([('template_id', '=', template.id)]).mapped('code') or [])
                final_code = code or False
                if final_code in used_codes:
                    i = 2
                    while f"{base_code}_{i}" in used_codes:
                        i += 1
                    final_code = f"{base_code}_{i}"[:64]
                dtype = self._infer_type(df[h])
                Attr.create({
                    "template_id": template.id,
                    "sequence": (j + 1) * 10,
                    "name": name,
                    "code": final_code,
                    "data_type": dtype,
                })
        if self.create_plans:
            if not template:
                template = self.env["bc.plan.template"].search([
                    ("subcampaign_id", "=", self.subcampaign_id.id)
                ], limit=1)
            if not template:
                raise UserError(_("No hay plantilla para crear planes."))
            attr_map = {}
            for attr in template.attribute_ids:
                keys = {attr.name, str(attr.name).lower()}
                if attr.code:
                    keys |= {attr.code, str(attr.code).lower()}
                for k in keys:
                    if k:
                        attr_map[k] = attr
            Plan = self.env["bc.plan"]
            Val = self.env["bc.plan.value"]
            for _, row in df.iterrows():
                pname = str(row.get(name_col) or "").strip()
                if not pname:
                    continue
                plan = Plan.create({
                    "name": pname,
                    "subcampaign_id": self.subcampaign_id.id,
                    "template_id": template.id,
                })
                for h in headers:
                    if h == name_col:
                        continue
                    attr = attr_map.get(h) or attr_map.get(str(h).lower())
                    if not attr:
                        continue
                    val = row.get(h)
                    if val is None or (isinstance(val, float) and str(val) == 'nan'):
                        continue
                    sval = str(val)
                    low = sval.strip().lower()
                    contains_alpha = any(c.isalpha() for c in sval) or ('%' in sval)
                    vals = {"plan_id": plan.id, "attribute_id": attr.id}
                    if not contains_alpha and attr.data_type in ("float", "integer"):
                        try:
                            num = float(sval.replace(" ", "").replace(",", "."))
                            if attr.data_type == "integer":
                                vals["value_int"] = int(round(num))
                            else:
                                vals["value_float"] = num
                        except Exception:
                            vals["value_char"] = sval
                    elif attr.data_type == "boolean":
                        vals["value_bool"] = low in ("si", "true", "1", "y")
                    else:
                        vals["value_char"] = sval
                    Val.create(vals)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Importacion completada"),
                "message": _("Hoja %s importada para %s") % (sheet_name, self.subcampaign_id.name),
                "sticky": False,
            },
        }

