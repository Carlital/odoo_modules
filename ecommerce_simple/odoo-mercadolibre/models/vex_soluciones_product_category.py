# -*- coding: utf-8 -*-
from odoo import fields, models, api

import logging

_logger = logging.getLogger(__name__)

class VexSolucinesInstaceInherit(models.Model):
    _inherit = "product.category"
    
    meli_category_id = fields.Char('Mercado Libre Category ID', readonly=True, index=True, help="ID de la Categoría en Mercado Libre")

    

class TrendWizard(models.TransientModel):
    _name = 'trend.wizard'

    category_id = fields.Many2one('product.category', string="Categoría")
    trends = fields.One2many('trend.wizard.line', 'wizard_id', string="Tendencias")

class TrendWizardLine(models.TransientModel):
    _name = 'trend.wizard.line'

    wizard_id = fields.Many2one('trend.wizard', string="Wizard")
    keyword = fields.Char(string="Keyword")
    url = fields.Char(string="URL")

class ProductCategoryRelation(models.Model):
    _name = 'product.category.relation'

    product_id = fields.Many2one('product.product', string="Product")
    product_categ_id = fields.Many2one(related='product_id.categ_id', store=True, string="Product Category")
    
class ProductCategory(models.Model):
    _inherit = 'product.category'

    product_count = fields.Integer(string="Product Count", compute='_compute_product_count', store=True)

    def action_show_fake_trends(self):
        # Reutilizamos el método de vex.instance
        if not self.meli_category_id:
            return
        
        vex_instance = self.env['vex.instance'].search([], limit=1)  # Supongamos que seleccionas una instancia específica
        return vex_instance.action_show_trends(self.meli_category_id, self.id)

    def _compute_product_count(self):
        for category in self:
            # Contamos los productos asociados a la categoría
            category.product_count = self.env['product.template'].search_count([('categ_id', '=', category.id)])

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """ Sobrecargamos el método search para devolver solo categorías con productos """
        # Agregamos una condición adicional para filtrar solo las categorías con productos
        args = args + [('product_count', '>', 0)]
        return super(ProductCategory, self).search(args, offset=offset, limit=limit, order=order, count=count)

