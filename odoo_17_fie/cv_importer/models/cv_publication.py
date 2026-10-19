from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class CvPublication(models.Model):
    _name = "cv.publication"
    _description = "Publicación Científica"
    _order = "publication_year desc, title"
    _rec_name = "title"

    active = fields.Boolean(
        string="Activo",
        default=True,
        help="Si está desmarcado, esta publicación será archivada y oculta de la mayoría de vistas"
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
        help="Empleado que es autor o coautor de esta publicación"
    )

    publication_type = fields.Selection(
        [
            ("article", "Artículo"),
            ("book", "Libro"),
            ("thesis", "Tesis"),
            ("congreso", "Congreso"),
            ("other", "Otro"),
        ],
        string="Tipo de Publicación",
        required=True,
        help="Tipo de publicación científica"
    )

    title = fields.Char(
        string="Título",
        required=True,
        size=500,
        index=True,
        help="Título completo de la publicación"
    )

    publication_year = fields.Integer(
        string="Año de Publicación",
        required=False,
        index=True,
        help="Año en que fue publicada"
    )

    publication_date = fields.Date(
        string="Fecha de Publicación",
        help="Fecha exacta de publicación (si está disponible)"
    )

    is_indexed = fields.Boolean(
        string="Indexado en Base de Datos",
        default=False,
        help="Verdadero si la publicación está indexada en Scopus, WoS, etc."
    )

    indexing_database = fields.Char(
        string="Base de Datos de Indexación",
        size=255,
        help="Base de datos donde está indexada la publicación (ej., Scopus, Web of Science, Scielo, Latindex)"
    )

    language = fields.Selection(
        [
            ("es", "Español"),
            ("en", "Inglés"),
            ("pt", "Portugués"),
            ("fr", "Francés"),
            ("de", "Alemán"),
            ("other", "Otro"),
        ],
        string="Idioma",
        default="other",
        help="Idioma de la publicación"
    )

    source = fields.Selection(
        [
            ("manual", "Manual"),
            ("import", "N8N Import"),
        ],
        string="Origen",
        default="manual",
        required=True,
        help="Origen de este registro de publicación"
    )

    citation_age_years = fields.Integer(
        string="Años Desde Publicación",
        compute="_compute_citation_age_years",
        store=False,
        help="Número de años desde la publicación"
    )

    _sql_constraints = [
        (
            "check_publication_year_valid",
            "CHECK(publication_year IS NULL OR publication_year = -1 OR "
            "(publication_year >= 1900 AND publication_year <= EXTRACT(YEAR FROM CURRENT_DATE) + 1))",
            "Publication year must be between 1900 and next year, or -1 for unknown.",
        ),
    ]


    def _normalize_nulls_to_dummy(self, vals):
        source = vals.get("source")
        if not source and self:
            source = self[0].source

        if source and source != "manual":
            return vals

        if "publication_year" in vals and vals["publication_year"] in (None, ""):
            vals["publication_year"] = -1

        return vals

    @api.model
    def create(self, vals):
        vals = self._normalize_nulls_to_dummy(dict(vals))
        return super().create(vals)

    def write(self, vals):
        vals = self._normalize_nulls_to_dummy(dict(vals))
        return super().write(vals)


    @api.depends("publication_year")
    def _compute_citation_age_years(self):
        """Calculate years since publication (ignora dummy -1)."""
        current_year = date.today().year
        for record in self:
            if record.publication_year and record.publication_year > 0:
                record.citation_age_years = current_year - record.publication_year
            else:
                record.citation_age_years = 0

    @api.constrains("publication_year")
    def _check_publication_year_range(self):
        """Validate publication year is within reasonable range."""
        current_year = date.today().year
        for record in self:
            if record.publication_year in (None, -1):
                continue

            if record.publication_year < 1900 or record.publication_year > current_year + 1:
                raise ValidationError(
                    _("Publication year must be between 1900 and %(next_year)s.\n"
                      "Current value: %(year)s\n"
                      "Title: %(title)s") % {
                        'next_year': current_year + 1,
                        'year': record.publication_year,
                        'title': record.title
                    }
                )

    def name_get(self):
        """Override name_get to show title + year (solo si año real > 0)."""
        result = []
        for record in self:
            name = record.title
            if record.publication_year and record.publication_year > 0:
                name = f"[{record.publication_year}] {name}"
            if len(name) > 80:
                name = name[:77] + "..."
            result.append((record.id, name))
        return result

    def _recompute_employee_metrics(self):
        """Recalcular métricas anuales del empleado asociado."""
        YearlyMetrics = self.env["cv.yearly.metrics"]
        employees = self.mapped("employee_id")
        for employee in employees:
            YearlyMetrics._compute_metrics_for_employee(employee)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._recompute_employee_metrics()
        return records

    def write(self, vals):
        result = super().write(vals)
        # Solo recalcular si cambió el año o el estado de indexación
        if "publication_year" in vals or "is_indexed" in vals or "employee_id" in vals:
            self._recompute_employee_metrics()
        return result

    def unlink(self):
        employees = self.mapped("employee_id")
        result = super().unlink()
        # Recalcular después de eliminar
        YearlyMetrics = self.env["cv.yearly.metrics"]
        for employee in employees:
            YearlyMetrics._compute_metrics_for_employee(employee)
        return result
