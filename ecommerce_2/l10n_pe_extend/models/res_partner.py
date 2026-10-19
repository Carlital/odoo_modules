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
    _inherit = 'res.partner'

    @api.onchange('l10n_pe_district')
    def _onchange_l10n_pe_district(self):
        if self.l10n_pe_district:
            if not self.city_id:
                self.city_id = self.l10n_pe_district.city_id.id
            self.zip = self.l10n_pe_district.code or False
            self.city = self.l10n_pe_district.name
