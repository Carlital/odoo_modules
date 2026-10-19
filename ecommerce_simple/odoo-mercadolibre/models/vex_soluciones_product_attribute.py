# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductAttributeInherit(models.Model):
    _inherit = 'product.attribute'

    meli_attribute_id = fields.Char(string="Mercado Libre Attribute ID", help="ID del atributo en Mercado Libre", readonly=True, index=True)
    
class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    meli_value_id = fields.Char(string="Mercado Libre Value ID", help="ID de valor del atributo en Mercado Libre", readonly=True, index=True)