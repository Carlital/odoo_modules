
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def print_report_label_price(self):
        data = {}
        return self.env.ref(
            "acs_product_labels_price.report_product_template_label_price_acs").report_action(
            self, data=data)

    @api.model
    def create(self, vals):
        product = super(ProductTemplate, self).create(vals)

        price_list_data = []
        main_pricelist = self.env['product.pricelist'].search(
            [('is_main', '=', True)], limit=1)
        if main_pricelist:
            price_list_data = [
                {
                    'pricelist_id': main_pricelist.id,
                    'product_tmpl_id': product.id,
                    'fixed_price': 0,
                    'min_quantity': 3,
                },
                {
                    'pricelist_id': main_pricelist.id,
                    'product_tmpl_id': product.id,
                    'fixed_price': 0,
                    'min_quantity': 1000,
                },
            ]

        cajon_pricelist = self.env['product.pricelist'].search(
            [('is_cajon', '=', True)], limit=1)
        if cajon_pricelist:
            price_list_data.append({
                'pricelist_id': cajon_pricelist.id,
                'product_tmpl_id': product.id,
                'fixed_price': 0,
                'min_quantity': 0,
            })

        for data in price_list_data:
            self.env['product.pricelist.item'].create(data)

        return product
