from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CvAcademicDegree(models.Model):
    _name = "cv.academic.degree"
    _description = "Título Académico"

    employee_id = fields.Many2one(
        "hr.employee",
        required=True,
        ondelete="cascade",
        string="Empleado",
    )

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

    degree_type = fields.Selection(
        selection=[
            ("primaria", "Primaria"),
            ("secundaria", "Educación Secundaria"),
            ("tecnico", "Técnico Superior"),
            ("tercer nivel", "Tercer Nivel"),
            ("cuarto nivel", "Cuarto Nivel"),
            ("no especificado", "No Especificado"),
        ],
        required=True,
        string="Tipo de Título",
    )

    degree_title = fields.Char(
        required=True,
        string="Título",
    )

    institution = fields.Char(
        required=True,
        string="Institución",
    )

    source = fields.Selection(
        [
            ("manual", "Manual"),
            ("import", "Import"),
        ],
        default="manual",
        required=True,
        string="Origen",
    )

    # NORMALIZACIÓN SOLO MANUAL

    def _normalize_manual_dummies(self, vals):
        source = vals.get("source")
        if not source and self:
            source = self[0].source

        if source and source != "manual":
            return vals

        sanitized = dict(vals)

        if "degree_title" in sanitized:
            if not (sanitized["degree_title"] or "").strip():
                sanitized["degree_title"] = "N/A"

        if "institution" in sanitized:
            if not (sanitized["institution"] or "").strip():
                sanitized["institution"] = "N/A"

        if "degree_type" in sanitized:
            if not sanitized["degree_type"]:
                sanitized["degree_type"] = "no especificado"

        return sanitized

    @api.model
    def create(self, vals):
        vals = self._normalize_manual_dummies(vals)
        return super().create(vals)

    def write(self, vals):
        vals = self._normalize_manual_dummies(vals)
        return super().write(vals)
