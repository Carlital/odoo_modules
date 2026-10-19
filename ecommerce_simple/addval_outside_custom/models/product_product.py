from odoo import api, fields, models, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    brand_id = fields.Many2one(
        comodel_name='wk.product.brand',
        related='product_tmpl_id.brand_id',
        string="Marca", 
        store=True)