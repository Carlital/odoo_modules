# -*- coding: utf-8 -*-
from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    signer_user_ids = fields.Many2many(
        comodel_name='res.users',
        string='Firmantes'
    )
