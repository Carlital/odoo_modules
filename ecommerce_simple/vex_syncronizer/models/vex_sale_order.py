from odoo import models, fields

class VexSaleOrder(models.Model):
    _inherit = 'sale.order'

    instance_id = fields.Many2one(
        'vex.instance',
        string='Instance',
        help='Instance to which this product template belongs')
    marketplace_ids = fields.Many2many(
        'vex.marketplace',
        string='Marketplaces',
        help='Marketplaces where this product template is available')

