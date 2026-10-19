from odoo import models, fields

class VexProductTemplate(models.Model):
    _inherit = 'product.template'

    instance_id = fields.Many2one(
        'vex.instance',
        string='Instance',
        help='Instance to which this product template belongs')
    marketplace_ids = fields.Many2many(
        'vex.marketplace',
        string='Marketplaces',
        help='Marketplaces where this product template is available')


class VexMarketplace(models.Model):
    _name = 'vex.marketplace'
    _description = 'Vex Marketplace' 
    _order = 'name'
    name = fields.Char(
        string='Name',
        required=True,
        help='Name of the marketplace')
    color_hex = fields.Char("Color HEX", default="#D6C7C7")  # como '#FF5733'
    color = fields.Integer("Color") 