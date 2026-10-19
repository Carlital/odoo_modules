# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = 'res.company'

    n2growth_logo = fields.Binary(string="N2Growth Logo")
    is_user_two = fields.Boolean(
        string="Is user two",
        readonly=True,
        compute="_compute_user_two")
    

    def _compute_user_two(self):
        if self.env.uid == 2:
            self.is_user_two = True
        else:
            self.is_user_two = False