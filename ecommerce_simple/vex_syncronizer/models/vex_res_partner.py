from odoo import models, fields

class VexResPartner(models.Model):
    _inherit = 'res.partner'

    instance_id = fields.Many2one(
        'vex.instance',
        string='Instance',
        help='Instance to which this product category belongs')
    marketplace_ids = fields.Many2many(
        'vex.marketplace',
        string='Marketplaces',
        help='Marketplaces where this product category is available')  
    