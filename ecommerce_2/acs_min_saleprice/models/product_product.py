# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    min_saleprice = fields.Monetary(
        string='Precio Mínimo de Venta',
        currency_field='currency_id',
        help="El precio de venta mínimo permitido para este producto. "
             "El sistema aplicará el valor más bajo entre este y cualquier regla de tarifa aplicable."
    )


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # El campo min_saleprice se hereda automáticamente de product.template
    # a través de la delegación (template_id).
    # Sin embargo, lo definimos explícitamente para poder usarlo directamente
    # en las búsquedas y lógica de este modelo si fuera necesario.
    min_saleprice = fields.Monetary(
        related='product_tmpl_id.min_saleprice',
        readonly=False,  # Permite editarlo a nivel de variante si se desea
        string='Precio Mínimo de Venta',
        currency_field='currency_id',
    )
