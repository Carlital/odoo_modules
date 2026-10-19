from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CvYearlyMetrics(models.Model):
    _name = "cv.yearly.metrics"
    _description = "Métricas Académicas Anuales"
    _order = "year desc, employee_id"
    _rec_name = "display_name"

    # Campo active para archivado
    active = fields.Boolean(
        string="Activo",
        default=True,
        help="Si está desmarcado, este registro de métricas será archivado"
    )

    # Relación con empleado
    employee_id = fields.Many2one(
        "hr.employee",
        string="Empleado",
        required=True,
        ondelete="cascade",
        index=True,
        help="Empleado para quien se calculan estas métricas"
    )

    # Año de referencia
    year = fields.Integer(
        string="Año",
        required=True,
        index=True,
        help="Año de referencia para las métricas agregadas"
    )

    # === PUBLICACIONES ===
    publications_count = fields.Integer(
        string="Total de Publicaciones",
        default=0,
        help="Número total de publicaciones en este año"
    )

    indexed_publications_count = fields.Integer(
        string="Publicaciones Indexadas",
        default=0,
        help="Número de publicaciones indexadas en Scopus/WoS"
    )

    # === PROYECTOS ===
    projects_count = fields.Integer(
        string="Total de Proyectos",
        default=0,
        help="Número total de proyectos en este año"
    )

    # === DISTINCIONES / LOGROS ===
    logros_count = fields.Integer(
        string="Logros",
        default=0,
        help="Numero de logros o distinciones recibidas en este año"
    )

    # === METADATOS ===
    last_computed_date = fields.Datetime(
        string="Último Cálculo",
        readonly=True,
        help="Fecha y hora en que estas métricas fueron calculadas por última vez"
    )

    computation_method = fields.Selection(
        [
            ("manual", "Manual Entry"),
            ("semi_automatic", "Semi-Automatic"),
        ],
        string="Método de Cálculo",
        default="manual",
        help="Método utilizado para calcular estas métricas"
    )

    # Campo computed para display
    display_name = fields.Char(
        string="Nombre de Visualización",
        compute="_compute_display_name",
        store=True
    )

    # SQL Constraints adicionales
    _sql_constraints = [
        (
            "employee_year_unique",
            "UNIQUE(employee_id, year)",
            "There can be only one record per employee and year."
        ),
        (
            "check_year_range",
            "CHECK(year >= 1950 AND year <= EXTRACT(YEAR FROM CURRENT_DATE) + 1)",
            "Year must be between 1950 and next year."
        ),
        (
            "check_publications_non_negative",
            "CHECK(publications_count >= 0)",
            "Publication counts cannot be negative."
        ),
    ]

    # =========================================================
    # DISPLAY NAME
    # =========================================================
    @api.depends("employee_id", "year")
    def _compute_display_name(self):
        """Compute display name for the record."""
        for record in self:
            if record.employee_id and record.year:
                record.display_name = f"{record.employee_id.name} - {record.year}"
            else:
                record.display_name = "New Metrics Record"

    # =========================================================
    # CONSTRAINTS
    # =========================================================
    @api.constrains("year", "publications_count", "projects_count", "logros_count")
    def _check_yearly_metrics_constraints(self):
        """Validate yearly metrics data."""
        current_year = fields.Date.today().year
        for rec in self:
            if rec.year < 1950 or rec.year > current_year + 1:
                raise ValidationError(
                    _("Year must be between 1950 and current year + 1.\n"
                      f"Employee: {rec.employee_id.name}\n"
                      f"Year: {rec.year}")
                )

            if rec.publications_count < 0:
                raise ValidationError(_("Publication counts cannot be negative."))

            if rec.logros_count < 0:
                raise ValidationError(_("Logros count cannot be negative."))

    # =========================================================
    # CÓMPUTO AUTOMÁTICO POR AÑO (SOLO SI HAY DATOS)
    # =========================================================

    @api.model
    def _compute_metrics_for_employee(self, employee):
        """
        Calcula las métricas por año para un empleado específico,
        SOLO para los años en los que tenga publicaciones o logros.
        """
        # PRIMERO: Eliminar todas las métricas existentes de este empleado
        existing_metrics = self.search([("employee_id", "=", employee.id)])
        if existing_metrics:
            existing_metrics.unlink()

        Publication = self.env["cv.publication"]
        Logros = self.env["cv.logros"]

        # ---------- PUBLICACIONES POR AÑO ----------
        # Obtener todas las publicaciones con año válido
        publications = Publication.search([
            ("employee_id", "=", employee.id),
            ("publication_year", "!=", False),
            ("publication_year", "!=", -1),
            ("publication_year", ">", 0)
        ])

        pubs_by_year = {}
        for pub in publications:
            year = pub.publication_year
            if year not in pubs_by_year:
                pubs_by_year[year] = {"total": 0, "indexed": 0}
            pubs_by_year[year]["total"] += 1
            if pub.is_indexed:
                pubs_by_year[year]["indexed"] += 1

        # ---------- LOGROS POR AÑO ----------
        logros = Logros.search([
            ("employee_id", "=", employee.id),
            ("award_year", "!=", False),
            ("award_year", "!=", -1),
            ("award_year", ">", 0)
        ])

        logros_by_year = {}
        for logro in logros:
            year = logro.award_year
            if year not in logros_by_year:
                logros_by_year[year] = 0
            logros_by_year[year] += 1

        # ---------- AÑOS EN LOS QUE SÍ HAY ALGO ----------
        years_with_data = set(pubs_by_year.keys()) | set(logros_by_year.keys())

        if not years_with_data:
            # No tiene nada, no creamos métricas
            return

        now = fields.Datetime.now()

        # Crear una métrica por cada año con datos
        for year in sorted(years_with_data):
            pub_info = pubs_by_year.get(year, {"total": 0, "indexed": 0})
            total_pubs = pub_info["total"]
            indexed_pubs = pub_info["indexed"]
            total_logros = logros_by_year.get(year, 0)

            vals = {
                "employee_id": employee.id,
                "year": year,
                "publications_count": total_pubs,
                "indexed_publications_count": indexed_pubs,
                "logros_count": total_logros,
                "projects_count": 0,
                "last_computed_date": now,
                "computation_method": "semi_automatic",
            }

            self.create(vals)

    @api.model
    def action_compute_all_yearly_metrics(self):
        """
        Acción para recalcular las métricas de TODOS los empleados.
        Solo se crean registros para años donde sí haya info
        (publicaciones o logros).
        """
        employees = self.env["hr.employee"].search([])
        for emp in employees:
            self._compute_metrics_for_employee(emp)
        return True
