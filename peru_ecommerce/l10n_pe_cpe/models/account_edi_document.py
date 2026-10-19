# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class AccountEdiDocument(models.Model):
    _inherit = [
        "account.edi.document",
        "pe.cpe.mixin",
    ]
    _name = "account.edi.document"

    #state = fields.Selection([('to_send', 'To Send'), ('sent', 'Sent'), ('to_cancel', 'To Cancel'), ('cancelled', 'Cancelled')])
    name = fields.Char(store = True)
    # attachment_id = fields.Many2one(readonly=True, states={'to_send': [('readonly', False)]})
    # move_id = fields.Many2one(readonly=True, states={'to_send': [('readonly', False)]})
    # edi_format_id = fields.Many2one(readonly=True, states={'to_send': [('readonly', False)]})
    # error = fields.Html(readonly=True, states={'to_send': [('readonly', False)]})

    pe_attachment_name = fields.Char("XML Name", related="attachment_id.name", readonly=True)
    pe_attachment_datas = fields.Binary("XML", related="attachment_id.datas", readonly=True)

    pe_response_name = fields.Char("Response Name", related="pe_response_id.name", readonly=True)
    pe_response_datas = fields.Binary("Response", related="pe_response_id.datas", readonly=True)