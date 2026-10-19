# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PeUIT(models.Model):
    _name = "pe.uit"
    _description = "Unidad Impositiva Tributaria"
    _order = 'due_date DESC'
    _rec_name = 'year'

    year = fields.Integer("Year", default=lambda self: fields.Date.today().year, required=True)
    due_date = fields.Date("Due Date", compute="_compute_date", store=True)
    start_date = fields.Date("Start Date", compute="_compute_date", store=True)
    amount = fields.Float("Amount")
    active = fields.Boolean("Active", default=True)
    description = fields.Char("Description")

    @api.constrains('year')
    def _check_uit_year(self):
        for uit_id in self:
            year = fields.Date.today().year
            if uit_id.year<1990 or uit_id.year>year+1:
                raise ValidationError(_("Unsupported period"))
            uits = self.search_count([('year','=',uit_id.year)])
            if uits>1:
                raise ValidationError(_("There is already a record in that period"))


    @api.depends("year")
    def _compute_date(self):
        for uit_id in self:
            if uit_id.year:
                start_date = "%d-01-01" % uit_id.year
                due_date = "%d-12-31" % uit_id.year
            else:
                start_date = False
                due_date = False
            uit_id.start_date = start_date
            uit_id.due_date = due_date

    @api.model
    def get_uit_by_date(self, date=None):
        if not date:
            date = fields.Date.today()
        uit_id = self.search([('start_date','>=',date),('due_date','<=',date)], limit=1)
        return uit_id.amount or 0.0


    @api.model
    def get_uit_by_year(self, year=None):
        if not year:
            year = fields.Date.today().year
        uit_id = self.search([('year', '=', year)], limit=1)
        return uit_id.amount or 0.0