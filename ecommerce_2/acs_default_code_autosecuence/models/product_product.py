# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('default_code') and not self._context.get('acs_code_generated'):
                sequence = self.env['ir.sequence'].next_by_code(
                    'product.default.code.sequence') or '/'
                vals['default_code'] = sequence

            if vals.get('default_code') and not vals.get('standard_name'):
                vals['standard_name'] = vals['default_code']

        products = super().create(vals_list)

        # Sincronizar al template por si el flujo quick-create no lo propagó
        for product in products:
            # Asegurar consistencia final: standard_name manda sobre default_code
            if product.standard_name and product.default_code != product.standard_name:
                product.default_code = product.standard_name

            tmpl = product.product_tmpl_id
            write_vals = {}
            # Si el código de la plantilla no coincide con el de la variante (ya corregido), actualízalo.
            if tmpl.default_code != product.default_code:
                write_vals['default_code'] = product.default_code
            # Asegura que el standard_name de la plantilla también sea consistente.
            if tmpl.standard_name != product.default_code:
                write_vals['standard_name'] = product.default_code
            if write_vals:
                tmpl.write(write_vals)

        return products
