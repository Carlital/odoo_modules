from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta


class CvWorkExperience(models.Model):
    _name = "cv.work.experience"
    _description = "Experiencia Laboral"
    _order = "start_date desc, end_date desc"
    _rec_name = "position"

    active = fields.Boolean(
        string="Activo",
        default=True,
        help="Si está desmarcado, este registro será archivado"
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
        help="Empleado que ocupó este cargo"
    )

    position = fields.Char(
        string="Cargo",
        required=True,
        size=255,
        help="Título del puesto o nombre del cargo (ej., 'Profesor Titular', 'Investigador Senior')"
    )

    company = fields.Char(
        string="Empresa / Institución",
        required=True,
        size=255,
        index=True,
        help="Nombre de la organización o institución"
    )

    department = fields.Char(
        string="Departamento",
        size=255,
        help="Departamento, facultad o división dentro de la organización"
    )

    start_date = fields.Date(
        string="Fecha de Inicio",
        required=False,
        help="Fecha en la que comenzó el cargo"
    )

    end_date = fields.Date(
        string="Fecha de Fin",
        help="Fecha en la que terminó el cargo (dejar vacío si es actual)"
    )

    responsibilities = fields.Text(
        string="Responsabilidades / Logros",
        help="Descripción de las principales responsabilidades, proyectos o logros en este rol"
    )

    duration_months = fields.Integer(
        string="Duración (meses)",
        compute="_compute_duration_months",
        store=True,
        help="Duración del empleo en meses (calculado desde las fechas). "
             "El valor -1 se usa como dummy cuando las fechas son desconocidas."
    )

    source = fields.Selection(
        [
            ("manual", "Manual"),
            ("import", "Import"),
        ],
        string="Origen",
        default="manual",
        required=True,
        help="Origen de este registro de datos"
    )

    display_period = fields.Char(
        string="Período",
        compute="_compute_display_period",
        store=True,
        help="Visualización formateada del período de empleo"
    )

    _sql_constraints = [
        (
            "check_start_year_reasonable",
            "CHECK(start_date IS NULL OR EXTRACT(YEAR FROM start_date) >= 1950)",
            "Start year must be 1950 or later.",
        ),
        (
            "check_duration_months_range",
            "CHECK(duration_months IS NULL OR duration_months >= -1)",
            "Duration (months) must be -1 (dummy), NULL or zero/positive.",
        ),
    ]


    @api.depends("start_date", "end_date")
    def _compute_duration_months(self):
        for record in self:
            if not record.start_date:
                record.duration_months = -1
                continue

            if not record.end_date:
                end = date.today()
            else:
                end = record.end_date

            delta = relativedelta(end, record.start_date)
            record.duration_months = delta.years * 12 + delta.months

    @api.depends("start_date", "end_date")
    def _compute_display_period(self):
        """Compute a formatted string for the employment period."""
        for record in self:
            if not record.start_date:
                record.display_period = "N/A"
                continue

            start_str = record.start_date.strftime("%m/%Y")

            if record.end_date:
                end_str = record.end_date.strftime("%m/%Y")
            else:
                end_str = "Present"

            record.display_period = f"{start_str} - {end_str}"


    @api.constrains("start_date", "end_date")
    def _check_date_validity(self):
        """Validate that end_date is after start_date."""
        for record in self:
            if record.start_date and record.end_date:
                if record.end_date < record.start_date:
                    raise ValidationError(
                        _("End date cannot be earlier than start date.\n"
                          f"Position: {record.position}\n"
                          f"Company: {record.company}\n"
                          f"Start: {record.start_date}\n"
                          f"End: {record.end_date}")
                    )

    @api.constrains("start_date")
    def _check_start_date_reasonable(self):
        """Validate that start_date is not too far in the past."""
        for record in self:
            if record.start_date and record.start_date.year < 1950:
                raise ValidationError(
                    _("Start date seems unrealistic (before 1950).\n"
                      f"Position: {record.position}\n"
                      f"Start Date: {record.start_date}")
                )

    def name_get(self):
        """Override name_get to show position + company."""
        result = []
        for record in self:
            name = f"{record.position}"
            if record.company:
                name += f" @ {record.company}"
            if record.display_period:
                name += f" ({record.display_period})"
            result.append((record.id, name))
        return result
