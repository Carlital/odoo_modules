# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re

class PeElectronicGuideBranch(models.Model):
    _name = "pe.electronic.guide.branch"
    _inherit = ['portal.mixin', 'mail.thread.main.attachment', 'mail.activity.mixin']
    _rec_name = 'complete_name'
    _description = "Electronic Guide Branch"

    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env.company)
    name = fields.Char("Name", required=True)
    country_id = fields.Many2one("res.country", "Country", store=True, compute="_compute_country_id")
    state_id = fields.Many2one("res.country.state", string='State', required=True)
    province_id = fields.Many2one('res.city', string='Province', required=True)
    district_id = fields.Many2one('l10n_pe.res.city.district', string='District', required=True)
    street = fields.Char("Street", required=True)
    code = fields.Char("Code", required=True)
    complete_name = fields.Char(
        'Complete Name', compute='_compute_complete_name',
        store=True)
    active = fields.Boolean("Active", default=True)

    @api.depends('name', 'code')
    def _compute_complete_name(self):
        for branch_id in self:
            if branch_id.name and branch_id.code:
                branch_id.complete_name = '%s / %s' % (branch_id.code, branch_id.name)
            else:
                branch_id.complete_name = branch_id.name

    @api.depends("company_id")
    def _compute_country_id(self):
        for branch_id in self:
            branch_id.country_id = branch_id.company_id.country_id.id

    @api.constrains('code')
    def _check_name(self):
        for branch_id in self:
            if not re.match(r'^[0-9]{4}$', branch_id.code):
                raise ValidationError("Ingrese un Codigo de Sucursal correcto por ejemplo 0000")
            if self.search([('code','=',branch_id.code),('company_id','=',branch_id.company_id.id),
                            ('id','!=',branch_id.id)]):
                raise ValidationError("El Codigo de Sucursal debe ser unico por compania")

    @api.model
    def create(self, vals):
        res = super(PeElectronicGuideBranch, self).create(vals)
        return res