# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################
from odoo import models, api

class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.model
    def _load_pos_data_models(self, config_id):
        models = super()._load_pos_data_models(config_id)
        models += ['mongo.server.config']
        return models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    @api.model
    def filter_products_by_config_categories(self, products):
        if not self.limit_categories or not self.iface_available_categ_ids:
            return products

        allowed_categ_ids = set(self.iface_available_categ_ids.ids)

        filtered_products = []
        for product in products:
            pos_categ_ids = []
            if isinstance(product, dict):
                raw_categs = product.get('pos_categ_ids', [])
                pos_categ_ids = [
                    cat[0] if isinstance(cat, (list, tuple)) else cat
                    for cat in raw_categs
                ]
            else:
                pos_categ_ids = product.pos_categ_ids.ids

            if any(cat_id in allowed_categ_ids for cat_id in pos_categ_ids):
                filtered_products.append(product)

        return filtered_products
