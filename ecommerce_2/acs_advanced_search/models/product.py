# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.osv import expression
import re

class ProductProduct(models.Model):
    _inherit = 'product.product'

    standard_name = fields.Char("Standard Name", related="product_tmpl_id.standard_name")

    def _compute_advanced_search(self):
        for r in self:
            r.advanced_search = ''

    
    @api.model
    def _load_pos_data_fields(self, config_id):
        res = super(ProductProduct,self)._load_pos_data_fields(config_id)
        res.append("standard_name")
        return res
    
    advanced_search = fields.Char(
        compute='_compute_advanced_search', compute_sudo=True,
        search='_search_advanced_search', )
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if limit == 0:
            return False
        if not name:
            return super().name_search(name, args, operator, limit)
        # search progressively by the most specific attributes
        positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
        is_positive = operator not in expression.NEGATIVE_TERM_OPERATORS
        products = self.browse()
        domain = args or []
        advanced_domain = self._search_advanced_search('ilike',name)
        if operator in positive_operators:
            products = self.search_fetch(expression.AND([domain, advanced_domain]), ['display_name'], limit=limit) \
                or self.search_fetch(expression.AND([domain, [('default_code', '=', name)]]), ['display_name'], limit=limit) \
                or self.search_fetch(expression.AND([domain, [('barcode', '=', name)]]), ['display_name'], limit=limit) 
            
        if not products:
            if is_positive:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                products = self.search_fetch(expression.AND([domain, [('default_code', operator, name)]]), ['display_name'], limit=limit)
                limit_rest = limit and limit - len(products)
                if limit_rest is None or limit_rest > 0:
                    products |= self.search_fetch(expression.AND([domain, [('id', 'not in', products.ids)], [('name', operator, name)]]), ['display_name'], limit=limit_rest)
            else:
                domain_neg = [
                    ('name', operator, name),
                    '|', ('default_code', operator, name), ('default_code', '=', False),
                ]
                products = self.search_fetch(expression.AND([domain, domain_neg]), ['display_name'], limit=limit)
        if not products and operator in positive_operators and (m := re.search(r'(\[(.*?)\])', name)):
            match_domain = [('default_code', '=', m.group(2))]
            products = self.search_fetch(expression.AND([domain, match_domain]), ['display_name'], limit=limit)
        if not products and (partner_id := self.env.context.get('partner_id')):
            # still no results, partner in context: search on supplier info as last hope to find something
            supplier_domain = [
                ('partner_id', '=', partner_id),
                '|',
                ('product_code', operator, name),
                ('product_name', operator, name),
            ]
            match_domain = [('product_tmpl_id.seller_ids', 'any', supplier_domain)]
            products = self.search_fetch(expression.AND([domain, match_domain]), ['display_name'], limit=limit)
        return [(product.id, product.display_name) for product in products.sudo()]
    

    def _search_advanced_search(self, operator, value):
        domain = []
        search_fields = ['name', 'default_code', 'standard_name', 'barcode']
        
        # Separar value por espacios o '%'
        terms = [term for term in value.replace('%', ' ').split() if term]
        
        if terms:
            or_conditions = []
            for field in search_fields:
                and_conditions = []
                for term in terms:
                    and_conditions.append((field, 'ilike', term))
                if len(and_conditions) > 1:
                    or_conditions.extend(['&'] * (len(and_conditions) - 1))
                or_conditions.extend(and_conditions)
            
            if len(or_conditions) > 1:
                domain.extend(['|'] * (len(search_fields) - 1))
            domain.extend(or_conditions)
        
        return domain

    
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    standard_name = fields.Char("Standard Name")

    def _compute_advanced_search(self):
        for r in self:
            r.advanced_search = ''
    
    advanced_search = fields.Char(
        compute='_compute_advanced_search', compute_sudo=True,
        search='_search_advanced_search', )
    
    def _search_advanced_search(self, operator, value):
        domain = []
        search_fields = ['name', 'default_code', 'standard_name', 'barcode']
        
        # Separar value por espacios o '%'
        terms = [term for term in value.replace('%', ' ').split() if term]
        
        if terms:
            or_conditions = []
            for field in search_fields:
                and_conditions = []
                for term in terms:
                    and_conditions.append((field, 'ilike', term))
                if len(and_conditions) > 1:
                    or_conditions.extend(['&'] * (len(and_conditions) - 1))
                or_conditions.extend(and_conditions)
            
            if len(or_conditions) > 1:
                domain.extend(['|'] * (len(search_fields) - 1))
            domain.extend(or_conditions)
        
        return domain
