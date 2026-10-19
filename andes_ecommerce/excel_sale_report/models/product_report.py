from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    cod_producto = fields.Char("Product Code")

class ProductProduct(models.Model):
    _inherit = 'product.product'

    cod_producto = fields.Char("Product Code", related="product_tmpl_id.cod_producto", store=True)
    precio_maximo = fields.Float(string="Max Price", compute="_compute_prices", store=True)
    precio_minimo = fields.Float(string="Min Price", compute="_compute_prices", store=True)
    precio_medio = fields.Float(string="Average Price", compute="_compute_prices", store=True)

    @api.depends('product_variant_ids.list_price')
    def _compute_prices(self):
        for product in self:
            prices = product.mapped('product_variant_ids.list_price')
            product.precio_maximo = max(prices) if prices else 0.0
            product.precio_minimo = min(prices) if prices else 0.0
            product.precio_medio = sum(prices) / len(prices) if prices else 0.0