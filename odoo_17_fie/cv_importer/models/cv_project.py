from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta


class CvProject(models.Model):
    _name = "cv.project"
    _description = "Proyecto de Investigación / Desarrollo"
    _order = "project_title"
    _rec_name = "project_title"

    active = fields.Boolean(
        string="Activo",
        default=True,
        help="Si está desmarcado, este proyecto será archivado y oculto de la mayoría de vistas"
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
        help="Empleado participante en este proyecto"
    )

    project_title = fields.Char(
        string="Título del Proyecto",
        required=True,
        size=500,
        index=True,
        help="Título completo del proyecto"
    )

    project_code = fields.Char(
        string="Código del Proyecto",
        size=100,
        help="Código o identificador oficial del proyecto (ej., PIC-18-ESPOCH-001)"
    )

    project_type = fields.Selection(
        [
            ("investigacion_e_innovacion", "Innovación"),
            ("vinculacion", "Vinculación"),
            ("servicio_comunitario", "Servicio Comunitario"),
            ("docencia", "Proyecto de Docencia"),
            ("otro", "Otro"),
        ],
        string="Tipo de Proyecto",
        required=True,
        default="investigacion_e_innovacion",
        help="Tipo o categoría del proyecto"
    )

    institution = fields.Char(
        string="Institución Ejecutora",
        size=255,
        default="ESPOCH",
        help="Institución principal que ejecuta el proyecto (ej., ESPOCH, Universidad Central)"
    )

    start_date = fields.Date(
        string="Fecha de Inicio",
        required=False,
        help="Fecha en la que comenzó el proyecto"
    )

    end_date = fields.Date(
        string="Fecha de Fin",
        help="Fecha en la que terminó el proyecto (dejar vacío si está en curso)"
    )

    source = fields.Selection(
        [
            ("manual", "Manual"),
            ("import", "Import"),
        ],
        string="Origen",
        default="manual",
        required=True,
        help="Origen de este registro de proyecto"
    )

    _sql_constraints = [
        (
            "check_start_year_reasonable",
            "CHECK(EXTRACT(YEAR FROM start_date) >= 1950)",
            "Start year must be 1950 or later.",
        ),
    ]

    def _normalize_dates_for_source(self, vals):
        source = vals.get("source")
        if not source and self:
            source = self[0].source

        if source != "import":
            return vals

        def _to_date(val):
            if not val:
                return None
            if isinstance(val, str):
                try:
                    return fields.Date.to_date(val)
                except Exception:
                    return None
            return val

        start = _to_date(vals.get("start_date")) if "start_date" in vals else None
        end = _to_date(vals.get("end_date")) if "end_date" in vals else None

        if not start and "start_date" not in vals and self:
            start = self[0].start_date
        if not end and "end_date" not in vals and self:
            end = self[0].end_date

        if start and start.year < 1950:
            vals["start_date"] = False
            start = None  

        if start and end and end < start:
            vals["end_date"] = False

        return vals

    @api.model
    def create(self, vals):
        vals = self._normalize_dates_for_source(dict(vals))
        return super().create(vals)

    def write(self, vals):
        vals = self._normalize_dates_for_source(dict(vals))
        return super().write(vals)


    @api.constrains("start_date", "end_date", "source")
    def _check_date_validity(self):
        """Validate that end_date is after start_date (solo para manual)."""
        for record in self:
            if record.source != "manual":
                continue

            if record.start_date and record.end_date:
                if record.end_date < record.start_date:
                    raise ValidationError(
                        _("End date cannot be earlier than start date.\n"
                          f"Project: {record.project_title}\n"
                          f"Start: {record.start_date}\n"
                          f"End: {record.end_date}")
                    )

    @api.constrains("start_date", "source")
    def _check_start_date_reasonable(self):
        """Validate that start_date is not too far in the past (solo manual)."""
        for record in self:
            if record.source != "manual":
                continue

            if record.start_date and record.start_date.year < 1950:
                raise ValidationError(
                    _("Start date seems unrealistic (before 1950).\n"
                      f"Project: {record.project_title}\n"
                      f"Start Date: {record.start_date}")
                )

    def name_get(self):
        """Override name_get to show project title + code."""
        result = []
        for record in self:
            name = record.project_title
            if record.project_code:
                name = f"[{record.project_code}] {name}"
            if len(name) > 80:
                name = name[:77] + "..."
            result.append((record.id, name))
        return result
