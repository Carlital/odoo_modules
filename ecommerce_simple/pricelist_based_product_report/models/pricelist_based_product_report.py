# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from datetime import datetime,timedelta
import pytz
import logging
_logger = logging.getLogger(__name__)



class ReportPricelistBasedProductDetails(models.AbstractModel):
    _name = 'report.pricelist_based_product_report.report_pricelist_products'
    _description = 'Pricelist Based Product Details Report'

    @api.model
    def get_product_details(self,partner=False):
        if partner:
            partner=self.env['res.partner'].sudo().browse(partner)
            product_pricelist = partner.property_product_pricelist
        else:
            product_pricelist=self.env.user.partner_id.property_product_pricelist
        products = {}
        products_added=[]
        product_base_pricelist=self.env['product.pricelist'].sudo().search([('name','=','Sugerido Público')],limit=1)
        product_template_obj=self.env['product.template'].sudo()
        product_product_obj=self.env['product.product'].sudo()
        for line in product_pricelist.item_ids:
            if line.applied_on == '0_product_variant' and line.product_id.id not in products_added:
                    vals={'product_id':line.product_id.id,'product_name':line.product_id.name,'code':line.product_id.default_code,'uom':'','qty':line.product_id.qty_available,'customer_price':0.0,'selling_price':0.0}
                    customer_price = product_pricelist._get_product_price(line.product_id,1,None,False)
                    if not customer_price:
                        customer_price = line.product_id.list_price
                    vals['customer_price'] =customer_price
                    if product_base_pricelist:
                        selling_price = product_base_pricelist._get_product_price(line.product_id, 1, None,False)
                        if not selling_price:
                            selling_price = line.product_id.list_price
                        vals['selling_price'] = selling_price
                    products[line.product_id.id] =vals
                    products_added.append(line.product_id.id)
            elif line.applied_on == '1_product':
                for rec in line.product_tmpl_id.product_variant_ids:
                    if rec.id not in products_added:
                        vals = {'product_id': rec.id, 'product_name': rec.name,
                                'code': rec.default_code, 'uom': rec.uom_id.name if rec.uom_id else '',
                                'qty': rec.qty_available, 'customer_price': 0.0, 'selling_price': 0.0}
                        customer_price = product_pricelist._get_product_price(rec, 1, None,False)
                        if not customer_price:
                            customer_price = rec.list_price
                        vals['customer_price'] = customer_price
                        if product_base_pricelist:
                            selling_price = product_base_pricelist._get_product_price(rec, 1, None,False)
                            if not selling_price:
                                selling_price = rec.list_price
                            vals['selling_price'] = selling_price
                        products[rec.id] = vals
                        products_added.append(rec.id)
            elif line.applied_on == '2_product_category':
                categ_ids = {}
                categ = line.categ_id
                while categ:
                    categ_ids[categ.id] = True
                    categ = categ.parent_id
                categ_ids = list(categ_ids)
                product_tmpl_recs=product_template_obj.search([('categ_id','in',categ_ids)])
                for product_tmpl in product_tmpl_recs:
                    for rec in product_tmpl.product_variant_ids:
                        if rec.id not in products_added:
                            vals = {'product_id': rec.id, 'product_name': rec.name,
                                    'code': rec.default_code, 'uom': rec.uom_id.name if rec.uom_id else '',
                                    'qty': rec.qty_available, 'customer_price': 0.0, 'selling_price': 0.0}
                            customer_price = product_pricelist._get_product_price(rec, 1, None,False)
                            if not customer_price:
                                customer_price = rec.list_price
                            vals['customer_price'] = customer_price
                            if product_base_pricelist:
                                selling_price = product_base_pricelist._get_product_price(rec, 1, False)
                                if not selling_price:
                                    selling_price = rec.list_price
                                vals['selling_price'] = selling_price
                            products[rec.id] = vals
                            products_added.append(rec.id)
            elif line.applied_on =='3_global':
                product_recs = product_product_obj.search([])
                for rec in product_recs:
                    if rec.id not in products_added:
                        vals = {'product_id': rec.id, 'product_name': rec.name,
                                'code': rec.default_code, 'uom': rec.uom_id.name if rec.uom_id else '',
                                'qty': rec.qty_available, 'customer_price': 0.0, 'selling_price': 0.0}
                        customer_price = product_pricelist._get_product_price(rec, 1, None,False)
                        if not customer_price:
                            customer_price = rec.list_price
                        vals['customer_price'] = customer_price
                        if product_base_pricelist:
                            selling_price = product_base_pricelist._get_product_price(rec, 1, None,False)
                            if not selling_price:
                                selling_price = rec.list_price
                            vals['selling_price'] = selling_price
                        products[rec.id] = vals
                        products_added.append(rec.id)
            elif line.applied_on == '4_brand':
                brand_ids = {}
                brand = line.brand_id
                brand_ids[brand.id] = True
                brand_ids = list(brand_ids)
                product_tmpl_recs = product_template_obj.search([('product_brand_id', 'in', brand_ids)])
                for product_tmpl in product_tmpl_recs:
                    for rec in product_tmpl.product_variant_ids:
                        if rec.id not in products_added and rec.website_published:
                            vals = {'product_id': rec.id, 'product_name': rec.name,
                                    'code': rec.default_code, 'uom': '',
                                    'qty': rec.qty_available, 'customer_price': 0.0, 'selling_price': 0.0,
                                    'barcode': rec.barcode or '',
                                    'brand': rec.product_brand_id.name if rec.product_brand_id else ''}
                            customer_price = product_pricelist._get_product_price(line.product_id,1,None,False)
                            if not customer_price:
                                customer_price = rec.list_price
                            vals['customer_price'] = customer_price
                            if product_base_pricelist:
                                selling_price = product_base_pricelist._get_product_price(line.product_id,1,None,False)
                                if not selling_price:
                                    selling_price = rec.list_price
                                vals['selling_price'] = selling_price
                            products[rec.id] = vals
                            products_added.append(rec.id)

        return {
            'products': sorted([{
                'product_id': product['product_id'],
                'product_name': product['product_name'],
                'code': product['code'],
                'quantity': product['qty'],
                'customer_price': product['customer_price'],
                'selling_price': product['selling_price'],
                'uom': product['uom'],

            } for line, product in products.items()], key=lambda l: l['product_name']),

        }

    
    def get_report_values(self, docids, data=None):
        data = dict(data or {})
        if data:
            data.update(self.get_product_details(data['partner_id']))
        else:
            data.update(self.get_product_details())
        return data
