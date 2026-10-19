# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import re
from io import BytesIO
import qrcode

class Warehouse(models.Model):
    _inherit = "stock.warehouse"

    pe_branch_id = fields.Many2one('res.company.branch', 'Branch')