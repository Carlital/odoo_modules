# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
import requests
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'