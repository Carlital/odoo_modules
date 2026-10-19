from odoo import models, fields

class VexProductCategory(models.Model):
    _inherit = 'product.category'

    instance_id = fields.Many2one(
        'vex.instance',
        string='Instance',
        help='Instance to which this product category belongs')
    marketplace_ids = fields.Many2many(
        'vex.marketplace',
        string='Marketplaces',
        help='Marketplaces where this product category is available')  
