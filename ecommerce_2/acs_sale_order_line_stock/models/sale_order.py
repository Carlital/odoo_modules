# -*- coding: utf-8 -*-
from odoo import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id_acs(self):
        """
        Cuando el almacén cambia, recalcula las cantidades de stock
        en todas las líneas del pedido.
        """
        if self.order_line:
            # Forzamos el recálculo de los campos compute
            self.order_line._compute_stock_quantities()

    def action_confirm(self):
        """
        Sobrescribe la acción de confirmar para guardar un snapshot
        del stock actual en los campos de almacenamiento.
        """
        # Forzamos el recálculo para tener valores actualizados
        self.order_line._compute_stock_quantities()

        # Guardamos el snapshot del stock para cada línea con productos stockables
        for line in self.order_line.filtered(lambda l: l.product_id and l.product_id.is_storable and not l.display_type):
            line.stock_actual_at_confirmation = line.stock_actual
            line.stock_virtual_at_confirmation = line.stock_virtual

        # Llamamos al método original para continuar el flujo normal
        return super(SaleOrder, self).action_confirm()
