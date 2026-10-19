# -*- coding: utf-8 -*-
#################################################################################
#
#	Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
from odoo import api, fields , models
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)

class website(models.Model):
	_inherit = 'website'


	def get_wk_brands(self,brand_set):
		return self.env['wk.product.brand'].sudo().browse(list(set(brand_set)))

	def get_filter_brand(self,wk_brands):
		filter_brand=''
		for wk_brand in wk_brands:
			filter_brand+='%s,'%(wk_brand.id)
		return filter_brand
		return ','.join(map(str,wk_brands.ids))
	
	def _get_brand_domain(self):
		attrib_brands = request.httprequest.args.getlist('attrib_brand')
		brand = request.httprequest.args.getlist('brand')
		brand_set=[]
		for attrib_brand in attrib_brands:
			attrib_brand_index = attrib_brand.split('-')[0]
			if brand:
				if brand[0]!=attrib_brand_index:
					brand_set+=[int(attrib_brand_index)]
			else:
				brand_set+=[int(attrib_brand_index)]

		_logger.info("-------------------------_get_brand_domain-----2---------%r",brand_set)
        #when user accss brand url
		if request.session.get('wk_brand'):
			try:
				brand_set.append(int(request.session['wk_brand']))
			except Exception as e:
				pass
		domain =[]
		if len(brand_set):
			domain += [('product_brand_id.id', 'in', list(brand_set))]
		return domain

	def sale_product_domain(self):
		return super().sale_product_domain()+self._get_brand_domain()
	

class product_template(models.Model):
	_inherit = 'product.template'

	product_brand_id = fields.Many2one(
		string='Brand',
		comodel_name="wk.product.brand"
	)

class Wk_ProductBrand(models.Model):
	_name = "wk.product.brand"
	_inherit = ['website.published.mixin']
	_description = "Website Product Brand"
	_order = "sequence asc"

	@api.depends('products')
	def _get_product_count(self):
		for rec in self:
			rec.total_products = len(rec.products.ids)

	name = fields.Char(
		string="Brand Name",required=True,
		translate=True
	)
	image = fields.Binary(
		string='product  image',
		help = " This Image will be visible to user in there shop  by brand onwebsite view !"
	)
	description = fields.Text(
		string ="Brand Description",
		translate=True
	)
	sequence = fields.Integer(
		string = "Sequence" ,
		help = "Gives the sequence order when displaying a list of brand onwebsite view.!"
	)
	products = fields.One2many(
		'product.template',
		'product_brand_id',
	)
	total_products = fields.Integer(
		string="Total no. of Products",
		compute=_get_product_count,
		# store=True
	)

	website_ribbon_id = fields.Many2one('product.ribbon', string='Ribbon')
	brand_banner = fields.Binary(string="Brand Banner")
	website_id = fields.Many2one('website', string="Website", ondelete='restrict')
	website_size_x = fields.Integer('Size X', default=1)
	website_size_y = fields.Integer('Size Y', default=1)
	website_style_ids = fields.Many2many('product.style', string='Styles', copy=False)

	country_of_origin = fields.Char(string="Country of Origin")

	@api.model
	def wk_activate_website_view(self):
		products_description = self.env.ref('website_sale.products_description')
		products_attributes = self.env.ref('website_sale.products_attributes')
		products_description.write(dict(active=1))
		products_attributes.write(dict(active=1))
		return True

	def _get_website_ribbon(self):
		return self.website_ribbon_id
