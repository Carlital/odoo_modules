# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Bizople Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

from odoo import models, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def _search_get_detail(self, website, order, options):
        res = super(ProductTemplate, self)._search_get_detail(website=website, order=order, options=options)
        stock_avail = options.get('show_instock')
        old_domain = res['base_domain']
        if stock_avail:
            old_domain.append([('qty_available', '>', 0)])
        return res