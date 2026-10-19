# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from librecpe import Servidor

class Partner(models.Model):
    _inherit = "res.partner"

    pe_guide_adv_driver_license = fields.Char("Adv Driver License")
    pe_guide_adv_register_number = fields.Char("Adv MTC Register Number")
