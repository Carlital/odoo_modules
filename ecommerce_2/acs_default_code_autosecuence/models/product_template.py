# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('default_code'):
                sequence = self.env['ir.sequence'].next_by_code(
                    'product.default.code.sequence') or '/'
                vals['default_code'] = sequence

            if vals.get('default_code') and not vals.get('standard_name'):
                vals['standard_name'] = vals['default_code']

        return super(ProductTemplate, self.with_context(acs_code_generated=True)).create(vals_list)
