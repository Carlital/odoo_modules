# -*- coding: utf-8 -*-

from odoo import api, fields, models

import logging

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_pe_auto_journal_select = fields.Boolean("Auto Journal Select", related='pos_config_id.pe_auto_journal_select',
                                                readonly=False, help="Automatically select the journal")
    pos_pe_force_journal_select = fields.Boolean("Force Journal Select", related='pos_config_id.pe_force_journal_select',
                                                 readonly=False, help="Force select the journal")
    pos_pe_journal_ids = fields.Many2many("account.journal", string="Invoice Sale Journals",
                                          related='pos_config_id.pe_journal_ids', readonly=False,
                                          domain="[('type', 'in', ['sale']),('company_id', '=', company_id)]")
