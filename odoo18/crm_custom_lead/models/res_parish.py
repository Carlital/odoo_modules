from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ResParish(models.Model):
    _name = "res.parish"
    _description = "Parroquia"
    _order = "name"
    _sql_constraints = [
        ('name_city_unique', 'unique(name, city_id)', 'La parroquia ya existe para esa ciudad.'),
    ]

    name = fields.Char(required=True)
    country_id = fields.Many2one(
        "res.country",
        required=True,
        default=lambda self: self.env["res.country"].search([("code", "=", "EC")], limit=1).id,
    )

    state_id = fields.Many2one("res.country.state")
    city_id = fields.Many2one("res.city", ondelete="cascade")
    zip = fields.Char()

    @api.onchange('country_id')
    def _onchange_country_id(self):
        for rec in self:
            if rec.state_id and rec.state_id.country_id and rec.country_id and rec.state_id.country_id.id != rec.country_id.id:
                rec.state_id = False
            if rec.city_id and rec.city_id.state_id and rec.state_id and rec.city_id.state_id.id != rec.state_id.id:
                rec.city_id = False

    @api.onchange('state_id')
    def _onchange_state_id(self):
        for rec in self:
            if rec.country_id and rec.state_id and rec.state_id.country_id.id != rec.country_id.id:
                rec.country_id = rec.state_id.country_id
            if rec.city_id and rec.city_id.state_id and rec.city_id.state_id.id != (rec.state_id.id if rec.state_id else False):
                rec.city_id = False

    @api.onchange('city_id')
    def _onchange_city_id(self):
        for rec in self:
            if rec.city_id:
                rec.state_id = rec.city_id.state_id
                rec.country_id = rec.city_id.state_id.country_id

    @api.constrains('country_id', 'state_id', 'city_id')
    def _check_geo_consistency(self):
        for rec in self:
            if not (rec.country_id and rec.state_id and rec.city_id):
                continue
            if rec.state_id.country_id.id != rec.country_id.id:
                raise ValidationError("La provincia no pertenece al país seleccionado.")
            if rec.city_id.state_id.id != rec.state_id.id:
                raise ValidationError("La ciudad no pertenece a la provincia seleccionada.")
