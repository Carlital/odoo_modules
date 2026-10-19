from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    list_price = fields.Float('Price')
    image_url = fields.Char('Image URL')
    description_sale = fields.Text('Description')
    category_id = fields.Many2one('product.category', string='Category', help="Categoría principal")
    subcategory_id = fields.Many2one('product.category', string='Subcategory', help="Subcategoría dentro de la categoría")
