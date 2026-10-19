from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class CvLogros(models.Model):
    _name = "cv.logros"
    _description = "Distinción / Premio / Reconocimiento"
    _order = "name desc"
    _rec_name = "name"

    active = fields.Boolean(
        string="Activo",
        default=True,
        help="Si está desmarcado, esta distinción será archivada"
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
        help="Empleado que recibió esta distinción"
    )

    tipo = fields.Selection(
        [
            ("artistico", "Artístico"),
            ("deportivo", "Deportivo"),
            ("academico", "Académico"),
            ("laboral", "Laboral"),
            ("other", "Other"),
        ],
        string="Tipo",
        required=True,
        default="academico",
        index=True,
        help="Tipo de logro o reconocimiento"
    )

    name = fields.Char(
        string="Nombre del Logro",
        required=True,
        size=500,
        index=True,
        help="Nombre completo del logro, premio o reconocimiento"
    )

    awarding_institution = fields.Char(
        string="Institución Otorgante",
        required=True,
        size=255,
        index=True,
        help="Organización o entidad que otorgó la distinción"
    )

    award_year = fields.Integer(
        string="Año",
        help="Año de la distinción"
    )

    source = fields.Selection(
        [
            ("manual", "Manual"),
            ("import", "Import"),
        ],
        string="Origen",
        required=True,
        default="manual",
        help="Origen de este registro de distinción"
    )

    _sql_constraints = [
        (
            "check_award_year_reasonable",
            "CHECK(award_year IS NULL OR award_year = -1 OR "
            "(award_year >= 1900 AND award_year <= EXTRACT(YEAR FROM CURRENT_DATE) + 1))",
            "Award year must be between 1900 and next year, or -1 for unknown.",
        ),
    ]

    def _normalize_nulls_to_dummy(self, vals):
        source = vals.get("source")
        if not source and self:
            source = self[0].source

        if source and source != "manual":
            return vals

        if "award_year" in vals and vals["award_year"] in (None, ""):
            vals["award_year"] = -1

        return vals

    @api.model
    def create(self, vals):
        vals = self._normalize_nulls_to_dummy(dict(vals))
        return super().create(vals)

    def write(self, vals):
        vals = self._normalize_nulls_to_dummy(dict(vals))
        return super().write(vals)


    @api.constrains("award_year")
    def _check_award_year_range(self):
        current_year = date.today().year
        for record in self:
            if record.award_year in (None, -1):
                continue

            if record.award_year < 1900 or record.award_year > current_year + 1:
                raise ValidationError(
                    _("Award year must be between 1900 and %(next_year)s.\n"
                      "Current value: %(year)s\n"
                      "Logro: %(name)s") % {
                          'next_year': current_year + 1,
                          'year': record.award_year,
                          'name': record.name
                      }
                )

    def name_get(self):
        """Override name_get to show name + year."""
        result = []
        for record in self:
            name = record.name
            if record.award_year and record.award_year != -1:
                name = f"[{record.award_year}] {name}"
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
        # Solo recalcular si cambió el año o el empleado
        if "award_year" in vals or "employee_id" in vals:
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
