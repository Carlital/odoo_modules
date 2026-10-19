# -*- coding: utf-8 -*-
from odoo import models, fields


class SaleReport(models.Model):
    """
    Inherits sale.report to add the pre-calculated date field for easier filtering.
    """
    _inherit = 'sale.report'

    date_order_filter = fields.Date(
        string='Fecha de Pedido (Filtro)',
        readonly=True,
    )

    def _select_sale(self):
        """
        Extend the main sales query to include the pre-calculated date field.
        """
        select_ = super()._select_sale()
        select_ += ", s.date_order_filter AS date_order_filter"
        return select_
