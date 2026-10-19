from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    acs_exclude_from_manufacturing = fields.Boolean(
        string='Excluir de Orden de Fabricación',
        help='Si está marcado, este producto y sus variantes no aparecerán en el reporte de Orden de Fabricación',
        default=False,
    )


class ProductProduct(models.Model):
    _inherit = 'product.product'

    bobina_number = fields.Char(string='Número de Bobina')
