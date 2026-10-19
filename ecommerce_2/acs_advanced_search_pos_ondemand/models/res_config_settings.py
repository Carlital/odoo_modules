# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    acs_pos_ondemand_top_category_id = fields.Many2one(
        "pos.category",
        string="Top Sellers POS Category",
        config_parameter="acs_advanced_search_pos_ondemand.top_category_id",
        help="Category where daily top-selling products will be added automatically.",
    )
    acs_pos_ondemand_top_limit = fields.Integer(
        string="Top Products Per Day",
        default=5,
        config_parameter="acs_advanced_search_pos_ondemand.top_limit",
        help="Maximum number of top-selling products to include each day.",
    )
    acs_pos_ondemand_min_qty = fields.Float(
        string="Minimum Daily Quantity",
        default=100.0,
        config_parameter="acs_advanced_search_pos_ondemand.min_qty",
        help="Only products with sold quantity equal or greater than this value are added.",
    )
