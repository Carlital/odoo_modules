# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SaleOrder(models.Model):
    """
    Inherits sale.order to add a date field for easier filtering.
    """
    _inherit = 'sale.order'

    date_order_filter = fields.Date(
        string='Fecha de Pedido (Filtro)',
        compute='_compute_date_order_filter',
        store=True,
        readonly=True,
        help="Technical field. Contains the date part of the 'Confirmation Date' for filtering purposes."
    )

    # Función de cómputo
    # Esta función se ejecutará cuando el valor de 'date_order' cambie.
    @api.depends('date_order')
    def _compute_date_order_filter(self):
        """
        Computes the value of date_order_filter by taking the date part
        from the date_order (DateTime) field.
        """
        for order in self:
            # Verificamos si date_order tiene un valor
            if order.date_order:
                # Asignamos solo la parte de la fecha al nuevo campo
                order.date_order_filter = order.date_order.date()
            else:
                # Si date_order está vacío, el campo de fecha también lo estará
                order.date_order_filter = False
