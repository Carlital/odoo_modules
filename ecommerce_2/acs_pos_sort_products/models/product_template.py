# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    acs_sort_pos_product = fields.Integer(
        string="POS Sort Priority",
        default=0,
        help="Set a priority for sorting products in the Point of Sale. "
        "Products with a higher number will appear first. "
        "Default is 0 (lowest priority). Use higher numbers for higher priority.",
    )
