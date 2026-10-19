# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # --- Campos de Stock en Tiempo Real ---
    stock_actual = fields.Float(
        string='Stock Actual',
        compute='_compute_stock_quantities',
        store=False,
        digits='Product Unit of Measure',
        help="Stock físico disponible (A Mano) en el almacén del pedido."
    )

    stock_virtual = fields.Float(
        string='Stock Virtual',
        compute='_compute_stock_quantities',
        store=False,
        digits='Product Unit of Measure',
        help="Stock previsto (A Mano - Salidas + Entradas) en el almacén del pedido."
    )

    # --- Campos para Snapshot al Confirmar ---
    stock_actual_at_confirmation = fields.Float(
        string='Stock Actual (C)',
        readonly=True,
        copy=False,
        digits='Product Unit of Measure',
        help="Stock físico que había en el almacén al momento de confirmar la venta."
    )

    stock_virtual_at_confirmation = fields.Float(
        string='Stock Virtual (C)',
        readonly=True,
        copy=False,
        digits='Product Unit of Measure',
        help="Stock previsto que había en el almacén al momento de confirmar la venta."
    )

    # --- Lógica de Cálculo ---
    @api.depends('product_id', 'product_id.is_storable', 'order_id.warehouse_id', 'product_uom')
    def _compute_stock_quantities(self):
        """
        Calcula el stock actual y virtual para cada línea de pedido.
        Usa la ubicación de stock del almacén seleccionado.
        Compatible con Odoo 18 usando el campo is_storable.
        """
        for line in self:
            line.stock_actual = 0.0
            line.stock_virtual = 0.0

            # Verificamos si tenemos la información necesaria
            if not line.product_id or line.display_type:
                continue

            # En Odoo 18: Solo calculamos para productos con control de stock
            if not line.product_id.is_storable:
                continue

            if not line.order_id.warehouse_id:
                continue

            warehouse = line.order_id.warehouse_id
            location = warehouse.lot_stock_id

            # Calculamos stock actual usando stock.quant filtrado por ubicación
            quants = self.env['stock.quant'].search([
                ('product_id', '=', line.product_id.id),
                ('location_id', 'child_of', location.id)
            ])
            qty_available = sum(quants.mapped('quantity'))

            # Calculamos stock virtual usando contexto de ubicación
            product_ctx = line.product_id.with_context(
                location=location.id,
                warehouse=warehouse.id
            )
            virtual_available = product_ctx.virtual_available

            # Convertimos a la UoM de la línea si es diferente
            if line.product_uom and line.product_uom != line.product_id.uom_id:
                qty_available = line.product_id.uom_id._compute_quantity(
                    qty_available,
                    line.product_uom,
                    raise_if_failure=False
                )
                virtual_available = line.product_id.uom_id._compute_quantity(
                    virtual_available,
                    line.product_uom,
                    raise_if_failure=False
                )

            line.stock_actual = qty_available
            line.stock_virtual = virtual_available
