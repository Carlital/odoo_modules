# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Bizople Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale

class BizopleWebsiteSale(WebsiteSale):
    def _get_search_options(
        self, category=None, attrib_values=None, pricelist=None, min_price=0.0, max_price=0.0, conversion_rate=1, **post
    ):
        res = super(BizopleWebsiteSale, self)._get_search_options(category, attrib_values, pricelist, min_price, max_price, conversion_rate, **post)
        show_instock = post.get('show_instock', False)
        res.update({
            'show_instock': show_instock
        })
        return res

    @http.route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>'
    ], type='http', auth="public", website=True, sitemap=WebsiteSale.sitemap_shop)
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, ppg=False, **post):
        res = super(BizopleWebsiteSale, self).shop(page, category, search, min_price, max_price, ppg, **post)

        show_instock = post.get('show_instock', False)
        keepQueryargs = res.qcontext['keep'].args
        keepQueryargs.update({
            'show_instock': show_instock,
        })
        
        res.qcontext.update({
            'show_instock': show_instock,
        })
        
        return res