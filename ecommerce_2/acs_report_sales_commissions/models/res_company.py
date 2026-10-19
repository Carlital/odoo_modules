# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    acs_commission = fields.Float(
        string='% Comisión',
        default=0.65,
        digits='Percentage',
        help="Porcentaje de comisión que se aplicará sobre la parte de venta de cada vendedor. "
        "Por ejemplo: 0.65 significa 65% de comisión."
    )

    acs_sales_meta_monthly_usd = fields.Monetary(
        string="Meta de Ventas Mensual en Dólares",
        default=15000.00,
        currency_field="currency_usd_id",
        help="Meta de ventas mensual en dólares por vendedor que no entrará en el cálculo; el excedente entrará en el cálculo de 0.65% de comisión.",
    )

    currency_usd_id = fields.Many2one(
        "res.currency",
        string="Moneda USD",
        default=lambda self: self.env.ref("base.USD"),
        readonly=True,
    )
