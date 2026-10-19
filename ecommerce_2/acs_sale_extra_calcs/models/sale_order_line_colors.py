from odoo import models, fields


class SaleOrderLineColors(models.Model):
    _name = 'sale.order.line.colors'
    _description = 'Gestión de Colores para Líneas de Venta'
    _order = 'name'

    name = fields.Char(string='Color', required=True, translate=True)
