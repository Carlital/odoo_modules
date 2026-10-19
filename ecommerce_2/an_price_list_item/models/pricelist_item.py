# -*- coding: utf-8 -*-
# Copyright 2025 Ahmed Nour (https://odoosa.net)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api

class PricelistItem(models.Model):
    """
    Extend product.pricelist.item to make it accessible through 
    our custom menu. No additional fields or methods are necessary
    as we're just making the existing functionality more accessible.
    """
    _inherit = 'product.pricelist.item'
    
    # The model already has all the necessary fields and functionality
    # We just need to inherit it to make it accessible through our menu
