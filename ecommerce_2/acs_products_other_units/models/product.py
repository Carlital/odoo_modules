from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    secondary_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='UoM Secundario'
    )

    secondary_stock = fields.Float(
        string='Stock Secundario',
        compute='_compute_secondary_stock',
        inverse='_inverse_secondary_stock',
        store=True,
        help="Stock calculado en la unidad de medida secundaria"
    )

    conversion_ratio = fields.Float(
        string='Relación de Conversión',
        default=1.0,
        help="Factor para convertir de UoM principal a secundario (Stock Secundario = Stock Principal × Ratio)"
    )

    @api.depends('qty_available', 'conversion_ratio')
    def _compute_secondary_stock(self):
        for record in self:
            record.secondary_stock = record.qty_available * record.conversion_ratio

    def _inverse_secondary_stock(self):
        for record in self:
            if record.qty_available != 0:
                record.conversion_ratio = record.secondary_stock / record.qty_available


class ProductProduct(models.Model):
    _inherit = 'product.product'

    secondary_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        related='product_tmpl_id.secondary_uom_id',
        string='UoM Secundario',
        readonly=False,
        store=True
    )

    secondary_stock = fields.Float(
        related='product_tmpl_id.secondary_stock',
        string='Stock Secundario',
        readonly=False,
        store=True
    )

    conversion_ratio = fields.Float(
        related='product_tmpl_id.conversion_ratio',
        string='Relación de Conversión',
        readonly=False,
        store=True
    )


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    secondary_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        related='product_id.secondary_uom_id',
        string='UoM Secundario',
        readonly=True,
        store=True
    )

    conversion_ratio = fields.Float(
        related='product_id.conversion_ratio',
        string='Relación de Conversión',
        readonly=True,
        store=True
    )

    secondary_stock = fields.Float(
        string='Stock Secundario',
        compute='_compute_secondary_stock',
        store=True,
        help="Stock calculado en la unidad de medida secundaria por ubicación"
    )

    @api.depends('inventory_quantity_auto_apply', 'conversion_ratio')
    def _compute_secondary_stock(self):
        for record in self:
            record.secondary_stock = record.inventory_quantity_auto_apply * record.conversion_ratio
