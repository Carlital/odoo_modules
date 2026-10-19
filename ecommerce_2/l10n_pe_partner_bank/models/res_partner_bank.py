# -*- encoding: utf-8 -*-
import requests
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from collections import OrderedDict
import re
import logging
_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner.bank'

    pe_acc_type = fields.Selection(selection=[('1','Ahorros'), ('2','Corriente'),('3','Detracciones')], string='Account Type')
    pe_acc_ncci = fields.Char(string='Number CCI')
    pe_no_print = fields.Boolean(string='No Print Report')