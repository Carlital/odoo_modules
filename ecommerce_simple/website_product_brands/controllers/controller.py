# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# License URL : <https://store.webkul.com/license.html/>
#################################################################################
import werkzeug
import logging

from odoo import SUPERUSER_ID
from odoo import http

from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website_sale.controllers.main import TableCompute, QueryURL

from odoo.http import request
from odoo.tools import lazy


_logger = logging.getLogger(__name__)

class WebsiteSale(WebsiteSale):
    @http.route(
        ['''/shop''',
         '''/shop/page/<int:page>''',
         '''/shop/category/<model("product.public.category"):category>''',
         '''/shop/category/<model("product.public.category"):category>/page/<int:page>''',
         '''/shop/brand/<model("wk.product.brand"):wk_brand>''',
          '''/shop/brand/<model("wk.product.brand"):wk_brand>/page/<int:page>'''],
        type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, ppg=False, **post):
        brand_set=[]
        wk_brand = post.get('wk_brand')
        if wk_brand:
            brand_set.append(wk_brand.id)
            request.session['wk_brand'] = wk_brand.id
        else:
            request.session['wk_brand'] = False

        response= super(WebsiteSale, self).shop(page=page, category=category, search=search, min_price=min_price, max_price=max_price, ppg=ppg, **post
        )

        brand =(post.get('brand')  and post.get('brand')) or False
        attrib_brands = request.httprequest.args.getlist('attrib_brand')
        for attrib_brand in attrib_brands:
            attrib_brand_index = attrib_brand.split('-')[0]
            if brand:
                if (brand!=attrib_brand_index):
                    brand_set+=[int(attrib_brand_index)]
            else:
                brand_set+=[int(attrib_brand_index)]
        response.qcontext['brand_set']= list(set(brand_set))
        response.qcontext['brand_rec']= request.env['wk.product.brand'].search([('website_published', '=', True), ('website_id', 'in', [request.website.id, False])])
        response.qcontext['wk_brands']= request.env['wk.product.brand'].browse(list(set(brand_set)))

        if ppg:
            try:
                ppg = int(ppg)
                post['ppg'] = ppg
            except ValueError:
                ppg = False
        if not ppg:
            ppg = request.env['website'].get_current_website().shop_ppg or 20

        ppr = request.env['website'].get_current_website().shop_ppr or 4

        qcontext = dict(response.qcontext)
        attrib_list = request.httprequest.args.getlist('attrib')
        url = "/shop"
        if search:
            post["search"] = search
        if category:
            category = request.env['product.public.category'].browse(int(category))
            url = "/shop/category/%s" % slug(category)
        if attrib_list:
            post['attrib'] = attrib_list
        search_count = len(qcontext.get('products'))
        pager = request.website.pager(url=url, total=qcontext.get('search_count'),
        page=page, step=ppg, scope=7, url_args=post)
        response.qcontext['pager'] = pager
        keep = QueryURL('/shop', category=category and int(category), search=search,
        attrib=attrib_list, order=post.get('order'),attrib_brand=attrib_brands)
        response.qcontext['keep'] = keep
        return response

    # def _get_search_domain(self, search, category, attrib_values,search_in_description=True):
    #     domain= super(WebsiteSale, self)._get_search_domain(search, category, attrib_values,search_in_description)
    #     domain = self._get_brand_domain(domain,search, category, attrib_values)

    #     return domain
    # def _get_brand_domain(self,domain,search, category, attrib_values):
    #     attrib_brands = request.httprequest.args.getlist('attrib_brand')
    #     brand = request.httprequest.args.getlist('brand')
    #     brand_set=[]
    #     for attrib_brand in attrib_brands:
    #         attrib_brand_index = attrib_brand.split('-')[0]
    #         if brand:
    #             if brand[0]!=attrib_brand_index:
    #                 brand_set+=[int(attrib_brand_index)]
    #         else:
    #             brand_set+=[int(attrib_brand_index)]

    #     if request.session.get('wk_brand'):
    #         try:
    #             brand_set.append(int(request.session['wk_brand']))
    #         except Exception as e:
    #             pass

    #     if len(brand_set):
    #         domain += [('product_brand_id.id', 'in', list(brand_set))]
    #     return domain

    def _get_brand(self, products):
        product_brands = []
        [product_brands.append(product.product_brand_id) for product in products if len(
            product.product_brand_id) and product.product_brand_id not in product_brands]
        return product_brands

    def _get_brand_search_domain(self, search):
        domain = [("website_published", "=", True),('website_id', 'in', [request.website.id, False])]
        if search:
            for srch in search.split(" "):
                domain += [('name', 'ilike', srch)]
        return domain

    @http.route(['/shop/brands','/shop/brands/page/<int:page>'],type='http', auth="public", website=True)
    def wk_brands_page(self,brand=False,page=0,search='', ppg=False, **post):
        if ppg:
            try:
                ppg = int(ppg)
                post["ppg"] = ppg
            except ValueError:
                ppg = False

        if not ppg:
            ppg = request.env['website'].get_current_website().shop_ppg or 20

        PPR = request.env['website'].get_current_website().shop_ppr or 4

        keep = QueryURL('/shop/brands', search=search)

        url = "/shop/brands"
        if search:
            post["search"] = search
        
        layout_mode = request.session.get('website_sale_shop_layout_mode')
        if not layout_mode:
            if request.website.viewref('website_sale.products_list_view').active:
                layout_mode = 'list'
            else:
                layout_mode = 'grid'

        wk_product_brand_obj = request.env['wk.product.brand'].search(self._get_brand_search_domain(search))
        wk_brands_count = len(wk_product_brand_obj)
        pager = request.website.pager(url=url, total=wk_brands_count, page=page, step=ppg, scope=7, url_args=post)
        offset = pager['offset']
        wk_product_brand_obj = wk_product_brand_obj[offset:offset+ppg]

        values = {
            'search': search,
            'pager': pager,
            'wk_brands_list': wk_product_brand_obj,
            'search_count': wk_brands_count,  # common for all searchbox
            'bins': TableCompute().process(wk_product_brand_obj, ppg, PPR),
            'ppg': ppg,
            'ppr': PPR,
            'rows':4,
            'keep': keep,
            'layout_mode': layout_mode,
        }
        return request.render("website_product_brands.wk_brands_page",values)

    def brand_category_domain(self,brand_id):
        brand_product = brand_id.products
        category_id = [i.public_categ_ids.id for i in brand_product]
        return [('id','in',category_id)]





    @http.route(['/product/brand/<int:brand>',
    '''/product/brand/<int:brand>/category/<model("product.public.category"):category>''',
    '''/product/brand/<int:brand>/category/<model("product.public.category"):category>/page/<int:page>'''
    ],type='http', auth="public", website=True)
    def wk_product_brand(self,brand=False, category=None ,page=0,search='',ppg=False,**post):
        Category = request.env['product.public.category']

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}

        if category:
            category = Category.search([('id', '=', int(category))], limit=1)
            if not category or not category.can_access_from_current_website():
                raise NotFound()
        else:
            category = Category

        if ppg:
            try:
                ppg = int(ppg)
                post["ppg"] = ppg
            except ValueError:
                ppg = False

        if not ppg:
            ppg = request.env['website'].get_current_website().shop_ppg or 20

        PPR = request.env['website'].get_current_website().shop_ppr or 4

        url = "/product/brand/" + str(brand)

        keep = QueryURL(url, category=category and int(category), search=search, attrib=attrib_list, order=post.get('order'))

        if search:
            post["search"] = search


        # website_domain = request.website.website_domain()
        
        if category:
            url = "/shop/category/%s" % slug(category)

        if brand:
            wk_brand = request.env["wk.product.brand"].search([('id','=',brand),('website_published','=',True)])
        if wk_brand:
            wk_brand_product = wk_brand.products.search(self._get_search_domain(search, category, attrib_values)+[('product_brand_id.id','=',brand)],order=self._get_search_order(post))
        product_count = len(wk_brand_product)

        categs_domain = [('parent_id', '=', False)] + self.brand_category_domain(wk_brand)
        if search:
            search_categories = Category.search([('product_tmpl_ids', 'in', wk_brand_product.ids)]).parents_and_self
            categs_domain.append(('id', 'in', search_categories.ids))
        else:
            search_categories = Category

        search_id = request.env["wk.product.brand"].search([('id','=',brand)])
        country_origin = search_id.country_of_origin

        categs = Category.search(categs_domain)


        pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
        offset = pager['offset']
        wk_brand_product = wk_brand_product[offset:offset+ppg]

        layout_mode = request.session.get('website_sale_shop_layout_mode')
        if not layout_mode:
            if request.website.viewref('website_sale.products_list_view').active:
                layout_mode = 'list'
            else:
                layout_mode = 'grid'

        ProductAttribute = request.env['product.attribute']
        if wk_brand_product:
            # get all products without limit
            attributes = ProductAttribute.search([('product_tmpl_ids', 'in', wk_brand_product.ids)])
        else:
            attributes = ProductAttribute.browse(attributes_ids)
        
        pricelist = request.website.pricelist_id
        products_prices = lazy(lambda: wk_brand.products._get_sales_prices(pricelist))

        values = {
            'search': search,
            'category': category,
            'pager': pager,
            'wk_brand': wk_brand,
            'brand_product':wk_brand_product,
            'search_count': wk_brand.total_products,  # common for all searchbox
            'bins': TableCompute().process(wk_brand_product, ppg, PPR),
            'ppg': ppg,
            'ppr': PPR,
            'rows':4,
            'categories': categs,
            'keep': keep,
            'layout_mode': layout_mode,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'attributes': attributes,
            'country_origin' : country_origin,
            'products_prices': products_prices,
            'get_product_prices': lambda product: lazy(lambda: products_prices[product.id]),

        }

        return request.render("website_product_brands.wk_product_brand_page",values)
