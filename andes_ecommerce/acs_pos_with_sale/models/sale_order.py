# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models,fields
from datetime import date


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def check_validate_orders(self):
        order_ids = self.env['sale.order'].search([('validity_date','<',date.today()),('state','in',('draft','sent'))])

        order_ids.action_cancel()


