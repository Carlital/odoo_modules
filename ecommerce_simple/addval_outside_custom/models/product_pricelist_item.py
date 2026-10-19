# -*- coding: utf-8 -*-

from odoo import _, fields, models, api
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.fields import Command
from odoo.tools import format_datetime, formatLang

from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

import logging

_logger = logging.getLogger(__name__)

class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    applied_on = fields.Selection(
        selection_add=[
            ('4_brand', "Marca")
        ],
        ondelete={'4_brand': 'set default'})
    
    brand_id = fields.Many2one(
        comodel_name='wk.product.brand', 
        string="Marca", 
        store=True)

    @api.depends('applied_on', 'categ_id', 'product_tmpl_id', 'product_id', 'brand_id','compute_price', 'fixed_price', \
        'pricelist_id', 'percent_price', 'price_discount', 'price_surcharge')
    def _compute_name_and_price(self):
        super(ProductPricelistItem, self)._compute_name_and_price()
        for item in self:
            if item.brand_id and item.applied_on == '4_brand':
                item.name = _("Marca: %s") % (item.brand_id.name)

    @api.constrains('product_id', 'product_tmpl_id', 'categ_id')
    def _check_product_consistency(self):
        super(ProductPricelistItem, self)._check_product_consistency()
        for item in self:
            if item.applied_on == "4_brand" and not item.brand_id:
                raise ValidationError(_("Please specify the brand for which this rule should be applied"))
            
    def _is_applicable_for(self, product, qty):
        self.ensure_one()
        if self.applied_on == '4_brand':
            return product.product_brand_id == self.brand_id
        else:
            return super(ProductPricelistItem, self)._is_applicable_for(product, qty)
    
