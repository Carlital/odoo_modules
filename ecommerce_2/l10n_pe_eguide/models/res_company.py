# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class Company(models.Model):
    _inherit = "res.company"

    pe_guide_ws_url = fields.Char("Guide Web Service URL")
    pe_guide_user = fields.Char("User")
    pe_guide_password = fields.Char("Password")
    pe_guide_client_id = fields.Char("Client Id")
    pe_guide_client_secret = fields.Char("Client Secret")
    pe_eguide_verify_url = fields.Char("Eguide Verify Url", default="https://e-factura.sunat.gob.pe/")