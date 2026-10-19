# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _

class PeRelatedDocument(models.Model):
    _name = "pe.related.document"
    _description = "SUNAT related document"

    name = fields.Char(string="Number")
    document_type = fields.Selection("_get_document_type", string="Document Type")
    move_id = fields.Many2one("account.move", "Move")
    @api.model
    def _get_document_type(self):
        return self.env['pe.catalog.12'].get_selection()