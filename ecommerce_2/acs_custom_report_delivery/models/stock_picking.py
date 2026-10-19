# -*- coding: utf-8 -*-
from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    acs_indications = fields.Text(string='Indicaciones')
    acs_coordinations = fields.Text(string='Coordinaciones')
    acs_history = fields.Text(string='Historia')
