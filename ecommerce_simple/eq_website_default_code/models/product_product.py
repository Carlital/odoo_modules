from odoo import api, fields, models, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_product_pvp = fields.Monetary(
        'PVP', default=1,currency_field='currency_id', compute='_compute_product_pvp'
    )


    @api.depends('list_price')
    def _compute_product_pvp(self):
        self.product_product_pvp =  self.lst_price*1.19