# -*- coding: utf-8 -*-

import json
import logging

from odoo import api, fields, models, _
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class SaleReference(models.Model):
    _name = "sale.reference"

    reference_number = fields.Char('Número')
    reference_date = fields.Date('Fecha')
    reference_doc_type_id = fields.Many2one('l10n_latam.document.type', 'Tipo Documento')
    sale_id = fields.Many2one('sale.order')