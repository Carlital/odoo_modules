from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_convertible_to_meter = fields.Boolean(
        string='Convertible a Metros',
        help='Indica si este producto puede convertirse de peso a metros lineales'
    )

    conversion_ratio = fields.Float(
        string='Ratio de Conversión (Peso/Metro)',
        digits='Product Unit of Measure',
        help='Cantidad de peso (kg) equivalente a 1 metro lineal. Ej: 3.0 significa que 3kg = 1 metro'
    )

    meter_counterpart_product_id = fields.Many2one(
        'product.product',
        string='Producto Contraparte (Metros)',
        help='Producto equivalente en metros lineales'
    )

    stock_in_meters = fields.Float(
        string='Stock en Metros',
        compute='_compute_stock_in_meters',
        help='Stock actual convertido a metros lineales (solo informativo)'
    )

    @api.depends('qty_available', 'conversion_ratio', 'is_convertible_to_meter')
    def _compute_stock_in_meters(self):
        for record in self:
            if record.is_convertible_to_meter and record.conversion_ratio > 0:
                record.stock_in_meters = record.qty_available / record.conversion_ratio
            else:
                record.stock_in_meters = 0.0

    @api.onchange('is_convertible_to_meter')
    def _onchange_is_convertible_to_meter(self):
        if not self.is_convertible_to_meter:
            self.conversion_ratio = 0.0
            self.meter_counterpart_product_id = False

    @api.constrains('conversion_ratio', 'is_convertible_to_meter')
    def _check_conversion_ratio(self):
        for record in self:
            if record.is_convertible_to_meter and record.conversion_ratio <= 0:
                raise ValidationError(
                    _('El ratio de conversión debe ser mayor que cero.'))

    @api.constrains('meter_counterpart_product_id', 'is_convertible_to_meter')
    def _check_meter_counterpart_product(self):
        for record in self:
            if record.is_convertible_to_meter and not record.meter_counterpart_product_id:
                raise ValidationError(
                    _('Debe seleccionar un producto contraparte en metros.'))


class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_convertible_to_meter = fields.Boolean(
        related='product_tmpl_id.is_convertible_to_meter')
    conversion_ratio = fields.Float(related='product_tmpl_id.conversion_ratio')
    meter_counterpart_product_id = fields.Many2one(
        related='product_tmpl_id.meter_counterpart_product_id')
    stock_in_meters = fields.Float(related='product_tmpl_id.stock_in_meters')
