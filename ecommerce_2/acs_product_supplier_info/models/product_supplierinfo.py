# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductSupplierinfo(models.Model):
    _name = 'product.supplierinfo'
    # Heredamos el modelo original y le añadimos las capacidades de chatter
    _inherit = ['product.supplierinfo', 'mail.thread', 'mail.activity.mixin']

    # 1. Creamos el nuevo campo y le activamos el seguimiento
    stock_condition = fields.Char(
        string="Stock del Proveedor",
        tracking=True
    )

    # 2. Añadimos seguimiento a los campos existentes.
    # No es necesario redefinir todo el campo, solo el atributo que queremos cambiar.
    min_qty = fields.Float(tracking=True)
    price = fields.Float(tracking=True)
    discount = fields.Float(tracking=True)
    product_name = fields.Char(tracking=True)
    product_code = fields.Char(tracking=True)
