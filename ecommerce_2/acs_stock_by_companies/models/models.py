# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    
    origin_country_ids = fields.Many2many(
        string='Pais de Procedencia',
        comodel_name='res.country',
        column1='company_id',
        column2='product_id',
    )
    
class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.depends('name')
    def _compute_display_name(self):
        for line in self:
            line.display_name = line.nickname or line.name