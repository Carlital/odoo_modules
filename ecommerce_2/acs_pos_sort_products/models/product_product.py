# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    acs_sort_pos_product = fields.Integer(
        related='product_tmpl_id.acs_sort_pos_product',
        string='POS Sort Priority',
        store=True,
        readonly=False
    )

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields = super()._load_pos_data_fields(config_id)
        fields.append('acs_sort_pos_product')
        return fields
