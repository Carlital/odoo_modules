from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CvLanguage(models.Model):
    _name = "cv.language"
    _description = "Competencia Lingüística"
    _order = "proficiency_level desc, language_name"
    _rec_name = "language_name"

    active = fields.Boolean(
        string="Activo",
        default=True,
        help="Si está desmarcado, este registro de idioma será archivado"
    )

    is_published = fields.Boolean(
        string="Publicado",
        default=True,
        help="Publicado en el sitio web/perfil público. Los borradores deben establecer esto en Falso."
    )

    employee_id = fields.Many2one(
        "hr.employee",
        string="Empleado",
        required=True,
        ondelete="cascade",
        index=True,
        help="Empleado que habla este idioma"
    )

    language_id = fields.Many2one(
        "res.lang",
        string="Idioma (Sistema)",
        help="Enlace al registro de idioma de Odoo, si está disponible (ej., en_US, es_ES)"
    )

    language_name = fields.Char(
        string="Nombre del Idioma",
        required=True,
        size=100,
        index=True,
        help="Nombre simple del idioma (ej. Inglés, Español, Francés)"
    )

    proficiency_level = fields.Selection(
        [
            ("native", "Nativo / Lengua Materna"),
            ("C2", "C2 - Usuario Competente (Dominio)"),
            ("C1", "C1 - Usuario Competente (Avanzado)"),
            ("B2", "B2 - Usuario Independiente (Intermedio Alto)"),
            ("B1", "B1 - Usuario Independiente (Intermedio)"),
            ("A2", "A2 - Usuario Básico (Elemental)"),
            ("A1", "A1 - Usuario Básico (Principiante)"),
        ],
        string="Nivel de Competencia General",
        required=True,
        default="B2",
        help="Marco Común Europeo de Referencia para las Lenguas (MCER) nivel"
    )

    writing_level = fields.Integer(
        string="Escritura (%)",
        help="Nivel de expresión escrita como porcentaje (0–100)"
    )

    speaking_level = fields.Integer(
        string="Habla (%)",
        help="Nivel de expresión oral como porcentaje (0–100)"
    )

    source = fields.Selection(
        [
            ("manual", "Manual"),
            ("import", "Import"),
        ],
        string="Origen",
        required=True,
        default="manual",
        help="Origen de este registro de idioma"
    )

    # =========================
    # Helpers internos
    # =========================
    def _normalize_nulls_to_dummy(self, vals):
        """Evita None/'' en porcentajes para source=manual usando -1 como dummy."""
        source = vals.get("source")
        if not source and self:
            source = self[0].source

        # Si es import, no tocamos nada aquí
        if source and source != "manual":
            return vals

        for field_name in ["writing_level", "speaking_level"]:
            if field_name in vals and vals[field_name] in (None, ""):
                vals[field_name] = -1
        return vals

    @api.model
    def _guess_proficiency_from_percentages(self, w, s):
        """Dado writing/speaking (0-100) devuelve el nivel MCER."""
        # Consideramos valores inválidos
        if w in (None, -1) or s in (None, -1):
            return False

        m = min(w, s)

        if m >= 98:
            return "native"
        elif m >= 95:
            return "C2"
        elif m >= 85:
            return "C1"
        elif m >= 75:
            return "B2"
        elif m >= 60:
            return "B1"
        elif m >= 45:
            return "A2"
        else:
            return "A1"

    # =========================
    # Overrides create / write
    # =========================
    @api.model
    def create(self, vals):
        vals = self._normalize_nulls_to_dummy(dict(vals))

        # Si no viene proficiency_level, lo calculamos a partir de los % (útil para import)
        if not vals.get("proficiency_level"):
            w = vals.get("writing_level")
            s = vals.get("speaking_level")
            guessed = self._guess_proficiency_from_percentages(w, s)
            if guessed:
                vals["proficiency_level"] = guessed

        return super().create(vals)

    def write(self, vals):
        vals = self._normalize_nulls_to_dummy(dict(vals))

        # Para no complicar mucho: si se hace un update masivo vía UI,
        # el onchange ya se encarga. Aquí solo aplicamos si el caller
        # no envía explicitamente proficiency_level pero sí modifica
        # los porcentajes Y el registro es de import.
        if "writing_level" in vals or "speaking_level" in vals:
            for rec in self:
                # Construimos los valores finales w/s para este registro
                w = vals.get("writing_level", rec.writing_level)
                s = vals.get("speaking_level", rec.speaking_level)

                if (not vals.get("proficiency_level")
                        and rec.source == "import"):
                    guessed = self._guess_proficiency_from_percentages(w, s)
                    if guessed:
                        # Escribimos solo en ese registro con el nivel calculado
                        super(CvLanguage, rec).write({
                            **vals,
                            "proficiency_level": guessed,
                        })
                    else:
                        super(CvLanguage, rec).write(vals)
            return True

        return super().write(vals)

    # =========================
    # Constraints
    # =========================
    @api.constrains("employee_id", "language_id", "language_name")
    def _check_unique_language(self):
        for rec in self:
            domain = [
                ("employee_id", "=", rec.employee_id.id),
                ("id", "!=", rec.id),
            ]
            if rec.language_id:
                domain.append(("language_id", "=", rec.language_id.id))
            else:
                domain.append(("language_id", "=", False))
            if rec.language_name:
                domain.append(("language_name", "=ilike", rec.language_name))
            existing = self.search(domain, limit=1)
            if existing:
                raise ValidationError(
                    _("This language already exists for this employee.\n"
                      f"Employee: {rec.employee_id.name}\n"
                      f"Language: {rec.language_name}")
                )

    @api.constrains("writing_level", "speaking_level")
    def _check_percentage_ranges(self):
        for rec in self:
            for field_name in ["writing_level", "speaking_level"]:
                val = getattr(rec, field_name)
                if val is None or val == -1:
                    continue

                if not (0 <= val <= 100):
                    raise ValidationError(_(
                        "The value for %s must be between 0 and 100.\nCurrent: %s"
                    ) % (field_name, val))

    # =========================
    # Onchange: nivel → %
    # =========================
    @api.onchange("proficiency_level")
    def _onchange_proficiency_level(self):
        mapping = {
            "native": {"w": 100, "s": 100},
            "C2":    {"w": 95,  "s": 95},
            "C1":    {"w": 85,  "s": 90},
            "B2":    {"w": 75,  "s": 80},
            "B1":    {"w": 65,  "s": 70},
            "A2":    {"w": 45,  "s": 50},
            "A1":    {"w": 25,  "s": 30},
        }
        for rec in self:
            if rec.proficiency_level in mapping:
                # Solo autocompletar si están vacíos / None / 0 / -1
                if rec.writing_level in (None, 0, -1) and rec.speaking_level in (None, 0, -1):
                    rec.writing_level = mapping[rec.proficiency_level]["w"]
                    rec.speaking_level = mapping[rec.proficiency_level]["s"]

    # =========================
    # Onchange: % → nivel
    # =========================
    @api.onchange("writing_level", "speaking_level")
    def _onchange_percentages_to_level(self):
        """Set overall proficiency based on writing/speaking percentages."""
        for rec in self:
            w = rec.writing_level
            s = rec.speaking_level
            guessed = self._guess_proficiency_from_percentages(w, s)
            if guessed:
                rec.proficiency_level = guessed

    # =========================
    # name_get personalizado
    # =========================
    def name_get(self):
        result = []
        for record in self:
            name = record.language_name
            if record.proficiency_level:
                name = f"{name} ({record.proficiency_level})"
            result.append((record.id, name))
        return result
