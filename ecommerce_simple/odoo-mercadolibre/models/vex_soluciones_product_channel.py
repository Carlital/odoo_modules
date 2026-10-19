# -*- coding: utf-8 -*-
from odoo import fields, models, api

class ProductChannel(models.Model):
    _name = 'product.channel'
    _description = 'Product Channel'

    name = fields.Char('Channel Name', required=True, unique=True)