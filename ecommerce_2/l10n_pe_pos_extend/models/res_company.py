# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = 'res.company'

    city_id = fields.Many2one('res.city', string='City of Address', compute="_compute_address")
    l10n_pe_district = fields.Many2one(
        'l10n_pe.res.city.district', string='District', compute="_compute_address",
        help='Districts are part of a province or city.')

    def _get_company_address_field_names(self):
        res = super(ResCompany, self)._get_company_address_field_names()
        return res + ['city_id', 'l10n_pe_district']

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields = super()._load_pos_data_fields(config_id)
        if self.env.company.country_id.code == "PE":
            fields += ["state_id", "zip", "street", "city_id", "l10n_pe_district"]
        return fields