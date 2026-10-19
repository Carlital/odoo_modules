# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import csv
from io import StringIO
import base64
from odoo.http import request
from unidecode import unidecode
import logging
_logger = logging.getLogger(__name__)


class PricelistBasedProductReportWizard(models.TransientModel):
    _name = 'pricelist.based.product.report.wizard'
    _description = 'Pricelist Based Product Report'

    partner_id=fields.Many2one('res.partner','Customer')
    json_file = fields.Text('File')
    filename = fields.Char('Filename')
    mimetype = fields.Char('Mimetype')

    def generate_report(self):
        csvfile = StringIO()
        writer = csv.writer(csvfile, delimiter=',')
        # write header
        header_list = [_("Código"), _("Descripción"),_("Código EAN"), _("Marca"), _( "URL Producto"), _("URL imagen"), _("Stock disponible"), _("Precio de venta"), _("Precio sugerido a público")]
        writer.writerow(header_list)
        if self.partner_id:
            product_pricelist = self.partner_id.property_product_pricelist
        else:
            product_pricelist=self.env.user.partner_id.property_product_pricelist
        products = {}
        products_added=[]
        product_base_pricelist=self.env['product.pricelist'].sudo().search([('name','=','Sugerido Público')],limit=1)
        product_template_obj=self.env['product.template'].sudo()
        product_product_obj=self.env['product.product'].sudo()
        for line in product_pricelist.item_ids:
            if line.applied_on == '0_product_variant' and line.product_id.website_published and line.product_id.id not in products_added:
                    product_url=request.httprequest.host_url+"shop/product/%s" % (line.product_id.product_tmpl_id.id,)
                    principal_image_url=request.httprequest.host_url+'web/image/product.product/%s/image_medium' % line.product_id.id
                    product_description = line.product_id.name
                    vals={'product_id':line.product_id.id,'product_name':product_description,'code':line.product_id.default_code,'uom':'','qty':line.product_id.qty_available,'customer_price':0.0,'selling_price':0.0,'barcode':line.product_id.barcode or '','brand':line.product_id.product_brand_id.name if line.product_id.product_brand_id else '','product_url':product_url,'principal_image_url':principal_image_url}
                    customer_price = product_pricelist._get_product_price(line.product_id,1,None,False)
                    if not customer_price:
                        customer_price = line.product_id.list_price
                    vals['customer_price'] =customer_price
                    if product_base_pricelist:
                        selling_price = product_base_pricelist._get_product_price(line.product_id,1,None,False)
                        if not selling_price:
                            selling_price = line.product_id.list_price
                        vals['selling_price'] = selling_price
                    products[line.product_id.id] =vals
                    products_added.append(line.product_id.id)
            elif line.applied_on == '1_product':
                for rec in line.product_tmpl_id.product_variant_ids:
                    if rec.id not in products_added and rec.website_published:
                        product_url = request.httprequest.host_url + "shop/product/%s" % (rec.product_tmpl_id.id,)
                        principal_image_url = request.httprequest.host_url + 'web/image/product.product/%s/image_1920' % rec.id
                        vals = {'product_id': rec.id, 'product_name': rec.name,
                                'code': rec.default_code, 'uom': '',
                                'qty': rec.qty_available, 'customer_price': 0.0, 'selling_price': 0.0,'barcode':rec.barcode or '','brand':rec.product_brand_id.name if rec.product_brand_id else '','product_url':product_url,'principal_image_url':principal_image_url}
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
                        if rec.id not in products_added and rec.website_published:
                            product_url = request.httprequest.host_url + "shop/product/%s" % (rec.product_tmpl_id.id,)
                            principal_image_url = request.httprequest.host_url + 'web/image/product.product/%s/image_1920' % rec.id
                            vals = {'product_id': rec.id, 'product_name': rec.name,
                                    'code': rec.default_code, 'uom': '',
                                    'qty': rec.qty_available, 'customer_price': 0.0, 'selling_price': 0.0,'barcode':rec.barcode or '','brand':rec.product_brand_id.name if rec.product_brand_id else '','product_url':product_url,'principal_image_url':principal_image_url}
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
            elif line.applied_on =='3_global':
                product_recs = product_product_obj.search([])
                for rec in product_recs:
                    if rec.id not in products_added and rec.website_published:
                        product_url = request.httprequest.host_url + "shop/product/%s" % (rec.product_tmpl_id.id,)
                        principal_image_url = request.httprequest.host_url + 'web/image/product.product/%s/image_1920' % rec.id
                        vals = {'product_id': rec.id, 'product_name': rec.name,
                                'code': rec.default_code, 'uom': '',
                                'qty': rec.qty_available, 'customer_price': 0.0, 'selling_price': 0.0,'barcode':rec.barcode or '','brand':rec.product_brand_id.name if rec.product_brand_id else '','product_url':product_url,'principal_image_url':principal_image_url}
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
            elif line.applied_on == '4_brand':
                brand_ids = {}
                brand = line.brand_id
                brand_ids[brand.id] = True
                brand_ids = list(brand_ids)
                product_tmpl_recs = product_template_obj.search([('product_brand_id', 'in', brand_ids)])
                for product_tmpl in product_tmpl_recs:
                    for rec in product_tmpl.product_variant_ids:
                        if rec.id not in products_added and rec.website_published:
                            product_url = request.httprequest.host_url + "shop/product/%s" % (rec.product_tmpl_id.id,)
                            principal_image_url = request.httprequest.host_url + 'web/image/product.product/%s/image_1920' % rec.id
                            vals = {'product_id': rec.id, 'product_name': rec.name,
                                    'code': rec.default_code, 'uom': '',
                                    'qty': rec.qty_available, 'customer_price': 0.0, 'selling_price': 0.0,
                                    'barcode': rec.barcode or '',
                                    'brand': rec.product_brand_id.name if rec.product_brand_id else '',
                                    'product_url': product_url, 'principal_image_url': principal_image_url}
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


        products=sorted([{
            'product_id': product['product_id'],
            'product_name': product['product_name'],
            'code': product['code'],
            'quantity': product['qty'],
            'customer_price': product['customer_price'],
            'selling_price': product['selling_price'],
            'uom': product['uom'],
            'barcode':product['barcode'],
            'brand':product['brand'],
            'product_url':product['product_url'],
            'principal_image_url':product['principal_image_url'],
        } for line, product in products.items()], key=lambda l: l['product_name'])


        for record in products:
            row_list = []
            row_list.append(record['code'])
            row_list.append(record['product_name'])
            row_list.append(record['barcode'])
            row_list.append(record['brand'])
            row_list.append(record['product_url'])
            row_list.append(record['principal_image_url'])
            quantity =str(int(record['quantity']))
            if record["uom"] != 'Unit(s)':
                quantity+=record["uom"]
            row_list.append(quantity)
            row_list.append(str(int(record["customer_price"])))
            row_list.append(str(int(record['selling_price']*1.19)))
            writer.writerow(row_list)
        filename = 'Descarga catálogo y stock.csv'
        self.write(
            {'json_file': base64.b64encode(csvfile.getvalue().encode('ISO-8859-1')),
             'filename': filename})
        # close file
        csvfile.close()
        action = {'name': 'Descarga catálogo y stock.csv', 'type': 'ir.actions.act_url',
                  'url': "web/content/?model=pricelist.based.product.report.wizard&id=" + str(
                      self.id) + "&filename_field=filename&field=json_file&download=true&filename=Descarga catálogo y stock.csv",
                  'target': 'new', }

        return action

    def generate_report_from_website(self):
        csvfile = StringIO()
        writer = csv.writer(csvfile, delimiter=',')
        # write header
        header_list = [_("Codigo"), _("Descripcion"),_("Codigo EAN"), _("Marca"), _( "URL Producto"), _("URL imagen"), _("Stock disponible"), _("Precio de venta"), _("Precio sugerido a publico")]
        writer.writerow(header_list)
        if self.partner_id:
            product_pricelist = self.partner_id.property_product_pricelist
        else:
            product_pricelist = self.env.user.partner_id.property_product_pricelist
        products = {}
        products_added = []
        product_base_pricelist = self.env['product.pricelist'].sudo().search([('name', '=', 'Sugerido Público')], limit=1)
        product_template_obj = self.env['product.template'].sudo()
        product_product_obj = self.env['product.product'].sudo()
        if product_base_pricelist:
            _logger.warning('ENTRO EN IF PRODUCT BASE')
            for line in product_base_pricelist.item_ids:
                _logger.warning('APPLIED_ON: %s', line.applied_on)
                if line.applied_on == '0_product_variant' and line.product_id.website_published and line.product_id.id not in products_added:
                    _logger.warning('ENTRO EN PRODUCT VARIANT')
                    product_url = request.httprequest.host_url + "shop/product/%s" % (line.product_id.product_tmpl_id.id,)
                    principal_image_url = request.httprequest.host_url + 'web/image/product.product/%s/image_medium' % line.product_id.id
                    vals = {'product_id': line.product_id.id, 'product_name': line.product_id.name,
                            'code': line.product_id.default_code,
                            'uom': '',
                            'qty': line.product_id.qty_available, 'customer_price': 0.0, 'selling_price': 0.0,
                            'barcode': line.product_id.barcode or '',
                            'brand': line.product_id.product_brand_id.name if line.product_id.product_brand_id else '',
                            'product_url': product_url, 'principal_image_url': principal_image_url}
                    _logger.warning('LINE.PRODUCT_ID: %s', line.product_id)
                    customer_price = product_pricelist._get_product_price(line.product_id,1,None,False)
                    if not customer_price:
                        customer_price = line.product_id.lst_price
                    vals['customer_price'] = customer_price
                    if product_base_pricelist:
                        selling_price = product_base_pricelist._get_product_price(line.product_id,1,None,False)
                        if not selling_price:
                            selling_price = line.product_id.lst_price
                        vals['selling_price'] = selling_price
                    products[line.product_id.id] = vals
                    products_added.append(line.product_id.id)
                elif line.applied_on == '1_product':
                    _logger.warning('ENTRO EN PRODUCT')
                    product_url = request.httprequest.host_url + "shop/product/%s" % (line.product_tmpl_id.id,)
                    principal_image_url = request.httprequest.host_url + 'web/image/product.product/%s/image_medium' % line.id
                    vals = {'product_id': line.product_tmpl_id.id, 'product_name': line.product_tmpl_id.name,
                            'code': line.product_tmpl_id.id.default_code, 'uom': '',
                            'qty': line.product_tmpl_id.id.qty_available, 'customer_price': 0.0, 'selling_price': 0.0,
                            'barcode': line.product_tmpl_id.id.barcode or '',
                            'brand': line.product_tmpl_id.product_brand_id.name if line.product_tmpl_id.id.product_brand_id else '', 'product_url': product_url,
                            'principal_image_url': principal_image_url}
                    _logger.warning('LINE.product_tmpl_id: %s', line.product_tmpl_id)
                    customer_price = product_pricelist._get_product_price(line.product_tmpl_id,1,None,False)
                    if not customer_price:
                        customer_price = line.product_tmpl_id.list_price 
                    vals['customer_price'] = customer_price
                    if product_base_pricelist:
                        selling_price = product_base_pricelist._get_product_price(line.product_tmpl_id,1,None,False)
                        if not selling_price:
                            selling_price = line.product_tmpl_id.list_price
                        vals['selling_price'] = selling_price
                    products[rec.id] = vals
                    products_added.append(rec.id)
                elif line.applied_on == '2_product_category':
                    _logger.warning('ENTRO EN PRODUCT CATEGORY')
                    categ_ids = {}
                    categ = line.categ_id
                    while categ:
                        categ_ids[categ.id] = True
                        categ = categ.parent_id
                    categ_ids = list(categ_ids)
                    product_tmpl_recs = product_template_obj.search([('categ_id', 'in', categ_ids)])
                    for product_tmpl in product_tmpl_recs:
                        for rec in product_tmpl.product_variant_ids:
                            if rec.id not in products_added and rec.website_published:
                                product_url = request.httprequest.host_url + "shop/product/%s" % (rec.product_tmpl_id.id,)
                                principal_image_url = request.httprequest.host_url + 'web/image/product.product/%s/image_1920' % rec.id
                                vals = {'product_id': rec.id, 'product_name': rec.name,
                                        'code': rec.default_code, 'uom': '',
                                        'qty': rec.qty_available, 'customer_price': 0.0, 'selling_price': 0.0,
                                        'barcode': rec.barcode or '',
                                        'brand': rec.product_brand_id.name if rec.product_brand_id else '',
                                        'product_url': product_url, 'principal_image_url': principal_image_url}
                                _logger.warning('LINE.PRODUCT_ID: %s', rec)
                                customer_price = product_pricelist._get_product_price(rec,1,None,False)
                                if not customer_price:
                                    customer_price = rec.lst_price
                                vals['customer_price'] = customer_price
                                if product_base_pricelist:
                                    selling_price = product_base_pricelist._get_product_price(rec,1,None,False)
                                    if not selling_price:
                                        selling_price = rec.lst_price
                                    vals['selling_price'] = selling_price
                                products[rec.id] = vals
                                products_added.append(rec.id)
                elif line.applied_on == '3_global':
                    _logger.warning('ENTRO EN GLOBAL ')
                    product_recs = product_product_obj.search([])
                    for rec in product_recs:
                        if rec.id not in products_added and rec.website_published:
                            product_url = request.httprequest.host_url + "shop/product/%s" % (rec.product_tmpl_id.id,)
                            principal_image_url = request.httprequest.host_url + 'web/image/product.product/%s/image_1920' % rec.id
                            vals = {'product_id': rec.id, 'product_name': rec.name,
                                    'code': rec.default_code, 'uom': '',
                                    'qty': rec.qty_available, 'customer_price': 0.0, 'selling_price': 0.0,
                                    'barcode': rec.barcode or '',
                                    'brand': rec.product_brand_id.name if rec.product_brand_id else '', 'product_url': product_url,
                                    'principal_image_url': principal_image_url}
                            _logger.warning('LINE.PRODUCT_ID: %s', rec)
                            customer_price = product_pricelist._get_product_price(rec,1,None,False)
                            if not customer_price:
                                customer_price = rec.lst_price
                            vals['customer_price'] = customer_price
                            if product_base_pricelist:
                                selling_price = product_base_pricelist._get_product_price(rec,1,None,False)
                                if not selling_price:
                                    selling_price = rec.lst_price
                                vals['selling_price'] = selling_price
                            products[rec.id] = vals
                            products_added.append(rec.id)
                elif line.applied_on == '4_brand':
                    _logger.warning('ENTRO EN PRODUCT BRAND')
                    brand_ids = {}
                    brand = line.brand_id
                    brand_ids[brand.id] = True
                    brand_ids = list(brand_ids)
                    product_tmpl_recs = product_template_obj.search([('product_brand_id', 'in', brand_ids)])
                    for product_tmpl in product_tmpl_recs:
                        for rec in product_tmpl.product_variant_ids:
                            if rec.id not in products_added and rec.website_published:
                                product_url = request.httprequest.host_url + "shop/product/%s" % (rec.product_tmpl_id.id,)
                                principal_image_url = request.httprequest.host_url + 'web/image/product.product/%s/image_1920' % rec.id
                                vals = {'product_id': rec.id, 'product_name': rec.name,
                                        'code': rec.default_code, 'uom': '',
                                        'qty': rec.qty_available, 'customer_price': 0.0, 'selling_price': 0.0,
                                        'barcode': rec.barcode or '',
                                        'brand': rec.product_brand_id.name if rec.product_brand_id else '',
                                        'product_url': product_url, 'principal_image_url': principal_image_url}
                                _logger.warning('LINE.PRODUCT_ID: %s', rec)
                                customer_price = product_pricelist._get_product_price(rec,1,None,False)
                                if not customer_price:
                                    customer_price = rec.lst_price
                                vals['customer_price'] = customer_price
                                if product_base_pricelist:
                                    selling_price = product_base_pricelist._get_product_price(rec,1,None,False)
                                    if not selling_price:
                                        selling_price = rec.lsst_price
                                    vals['selling_price'] = selling_price
                                products[rec.id] = vals
                                products_added.append(rec.id)
        else:       
            for line in product_pricelist.item_ids:
                _logger.warning('APPLIED_ON: %s', line.applied_on)
                if line.applied_on == '0_product_variant' and line.product_id.website_published and line.product_id.id not in products_added:
                    _logger.warning('ENTRO EN PRODUCT VARIANT')
                    product_url = request.httprequest.host_url + "shop/product/%s" % (line.product_id.product_tmpl_id.id,)
                    principal_image_url = request.httprequest.host_url + 'web/image/product.product/%s/image_medium' % line.product_id.id
                    vals = {'product_id': line.product_id.id, 'product_name': line.product_id.name,
                            'code': line.product_id.default_code,
                            'uom': '',
                            'qty': line.product_id.qty_available, 'customer_price': 0.0, 'selling_price': 0.0,
                            'barcode': line.product_id.barcode or '',
                            'brand': line.product_id.product_brand_id.name if line.product_id.product_brand_id else '',
                            'product_url': product_url, 'principal_image_url': principal_image_url}
                    _logger.warning('LINE.PRODUCT_ID: %s', line.product_id)
                    customer_price = product_pricelist._get_product_price(line.product_id,1,None,False)
                    if not customer_price:
                        customer_price = line.product_id.lst_price
                    vals['customer_price'] = customer_price
                    if product_base_pricelist:
                        selling_price = product_base_pricelist._get_product_price(line.product_id,1,None,False)
                        if not selling_price:
                            selling_price = line.product_id.lst_price
                        vals['selling_price'] = selling_price
                    products[line.product_id.id] = vals
                    products_added.append(line.product_id.id)
                elif line.applied_on == '1_product':
                    _logger.warning('ENTRO EN PRODUCT')
                    product_url = request.httprequest.host_url + "shop/product/%s" % (line.product_tmpl_id.id,)
                    principal_image_url = request.httprequest.host_url + 'web/image/product.product/%s/image_medium' % line.id
                    vals = {'product_id': line.product_tmpl_id.id, 'product_name': line.product_tmpl_id.name,
                            'code': line.product_tmpl_id.id.default_code, 'uom': '',
                            'qty': line.product_tmpl_id.id.qty_available, 'customer_price': 0.0, 'selling_price': 0.0,
                            'barcode': line.product_tmpl_id.id.barcode or '',
                            'brand': line.product_tmpl_id.product_brand_id.name if line.product_tmpl_id.id.product_brand_id else '', 'product_url': product_url,
                            'principal_image_url': principal_image_url}
                    _logger.warning('LINE.product_tmpl_id: %s', line.product_tmpl_id)
                    customer_price = product_pricelist._get_product_price(line.product_tmpl_id,1,None,False)
                    if not customer_price:
                        customer_price = line.product_tmpl_id.list_price 
                    vals['customer_price'] = customer_price
                    if product_base_pricelist:
                        selling_price = product_base_pricelist._get_product_price(line.product_tmpl_id,1,None,False)
                        if not selling_price:
                            selling_price = line.product_tmpl_id.list_price
                        vals['selling_price'] = selling_price
                    products[rec.id] = vals
                    products_added.append(rec.id)
                elif line.applied_on == '2_product_category':
                    _logger.warning('ENTRO EN PRODUCT CATEGORY')
                    categ_ids = {}
                    categ = line.categ_id
                    while categ:
                        categ_ids[categ.id] = True
                        categ = categ.parent_id
                    categ_ids = list(categ_ids)
                    product_tmpl_recs = product_template_obj.search([('categ_id', 'in', categ_ids)])
                    for product_tmpl in product_tmpl_recs:
                        for rec in product_tmpl.product_variant_ids:
                            if rec.id not in products_added and rec.website_published:
                                product_url = request.httprequest.host_url + "shop/product/%s" % (rec.product_tmpl_id.id,)
                                principal_image_url = request.httprequest.host_url + 'web/image/product.product/%s/image_1920' % rec.id
                                vals = {'product_id': rec.id, 'product_name': rec.name,
                                        'code': rec.default_code, 'uom': '',
                                        'qty': rec.qty_available, 'customer_price': 0.0, 'selling_price': 0.0,
                                        'barcode': rec.barcode or '',
                                        'brand': rec.product_brand_id.name if rec.product_brand_id else '',
                                        'product_url': product_url, 'principal_image_url': principal_image_url}
                                _logger.warning('LINE.PRODUCT_ID: %s', rec)
                                customer_price = product_pricelist._get_product_price(rec,1,None,False)
                                if not customer_price:
                                    customer_price = rec.lst_price
                                vals['customer_price'] = customer_price
                                if product_base_pricelist:
                                    selling_price = product_base_pricelist._get_product_price(rec,1,None,False)
                                    if not selling_price:
                                        selling_price = rec.lst_price
                                    vals['selling_price'] = selling_price
                                products[rec.id] = vals
                                products_added.append(rec.id)
                elif line.applied_on == '3_global':
                    _logger.warning('ENTRO EN GLOBAL ')
                    product_recs = product_product_obj.search([])
                    for rec in product_recs:
                        if rec.id not in products_added and rec.website_published:
                            product_url = request.httprequest.host_url + "shop/product/%s" % (rec.product_tmpl_id.id,)
                            principal_image_url = request.httprequest.host_url + 'web/image/product.product/%s/image_1920' % rec.id
                            vals = {'product_id': rec.id, 'product_name': rec.name,
                                    'code': rec.default_code, 'uom': '',
                                    'qty': rec.qty_available, 'customer_price': 0.0, 'selling_price': 0.0,
                                    'barcode': rec.barcode or '',
                                    'brand': rec.product_brand_id.name if rec.product_brand_id else '', 'product_url': product_url,
                                    'principal_image_url': principal_image_url}
                            _logger.warning('LINE.PRODUCT_ID: %s', rec)
                            customer_price = product_pricelist._get_product_price(rec,1,None,False)
                            if not customer_price:
                                customer_price = rec.lst_price
                            vals['customer_price'] = customer_price
                            if product_base_pricelist:
                                selling_price = product_base_pricelist._get_product_price(rec,1,None,False)
                                if not selling_price:
                                    selling_price = rec.lst_price
                                vals['selling_price'] = selling_price
                            products[rec.id] = vals
                            products_added.append(rec.id)
                elif line.applied_on == '4_brand':
                    _logger.warning('ENTRO EN PRODUCT BRAND')
                    brand_ids = {}
                    brand = line.brand_id
                    brand_ids[brand.id] = True
                    brand_ids = list(brand_ids)
                    product_tmpl_recs = product_template_obj.search([('product_brand_id', 'in', brand_ids)])
                    for product_tmpl in product_tmpl_recs:
                        for rec in product_tmpl.product_variant_ids:
                            if rec.id not in products_added and rec.website_published:
                                product_url = request.httprequest.host_url + "shop/product/%s" % (rec.product_tmpl_id.id,)
                                principal_image_url = request.httprequest.host_url + 'web/image/product.product/%s/image_1920' % rec.id
                                vals = {'product_id': rec.id, 'product_name': rec.name,
                                        'code': rec.default_code, 'uom': '',
                                        'qty': rec.qty_available, 'customer_price': 0.0, 'selling_price': 0.0,
                                        'barcode': rec.barcode or '',
                                        'brand': rec.product_brand_id.name if rec.product_brand_id else '',
                                        'product_url': product_url, 'principal_image_url': principal_image_url}
                                _logger.warning('LINE.PRODUCT_ID: %s', rec)
                                customer_price = product_pricelist._get_product_price(rec,1,None,False)
                                if not customer_price:
                                    customer_price = rec.lst_price
                                vals['customer_price'] = customer_price
                                if product_base_pricelist:
                                    selling_price = product_base_pricelist._get_product_price(rec,1,None,False)
                                    if not selling_price:
                                        selling_price = rec.lsst_price
                                    vals['selling_price'] = selling_price
                                products[rec.id] = vals
                                products_added.append(rec.id)

        products = sorted([{
            'product_id': product['product_id'],
            'product_name': unidecode(product['product_name']),
            'code': product['code'],
            'quantity': product['qty'],
            'customer_price': round(product['customer_price'],0),
            'selling_price': round(product['selling_price'],0),
            'uom': product['uom'],
            'barcode': product['barcode'],
            'brand': product['brand'],
            'product_url': product['product_url'],
            'principal_image_url': product['principal_image_url'],
        } for line, product in products.items()], key=lambda l: l['product_name'])

        for record in products:
            row_list = []
            row_list.append(record['code'])
            row_list.append(record['product_name'])
            row_list.append(record['barcode'])
            row_list.append(record['brand'])
            row_list.append(record['product_url'])
            row_list.append(record['principal_image_url'])
            quantity = str(int(record['quantity']))
            if record["uom"] != 'Unit(s)':
                quantity += record["uom"]
            row_list.append(quantity)
            row_list.append(str(record["customer_price"]))
            result = int(record['selling_price'])*1.19
            row_list.append(str(result))
            writer.writerow(row_list)
        
        filename = 'Pricelist Based Product.csv'


        csv_data = csvfile.getvalue()

        # Print CSV data
        _logger.warning('DEOCDE ISO 8859: %s',csv_data)

        base64_data = base64.b64encode(csv_data.encode('utf-8'))  
        
 
        self.write({
            'json_file': csv_data,
            'filename': filename,
            'mimetype': 'text/csv'})
        # close file
        
        csvfile.close()
        # action = {'name': 'Pricelist Based Product.csv', 'type': 'ir.actions.act_url',
        #           'url': "web/content/?model=pricelist.based.product.report.wizard&id=" + str(
        #               self.id) + "&filename_field=filename&field=json_file&download=true&filename=Pricelist Based Product.csv",
        #           'target': 'new', }
        url= "web/content/?model=pricelist.based.product.report.wizard&id=" + str(self.id) + "&filename_field=filename&field=json_file&download=true&filename=Pricelist Based Product.csv"
        return self

    # @api.multi
    # def generate_report(self):
    #     data = {'partner_id':self.partner_id.id}
    #     return self.env.ref('pricelist_based_product_report.pricelist_based_product_details_report').report_action([], data=data)
