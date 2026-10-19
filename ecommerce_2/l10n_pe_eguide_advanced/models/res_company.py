# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from librecpe import Servidor

class Company(models.Model):
    _inherit = "res.company"

    pe_guide_adv_ws_url = fields.Char("Guide Web Service URL", default="https://api-cpe.sunat.gob.pe/")
    pe_guide_adv_user = fields.Char("EGA User")
    pe_guide_adv_password = fields.Char("EGA Password")
    pe_guide_adv_client_id = fields.Char("EGA Client Id")
    pe_guide_adv_client_secret = fields.Char("EGA Client Secret")
    pe_guide_adv_verify_url = fields.Char("EGA Eguide Verify Url", default="https://e-factura.sunat.gob.pe/")
    pe_guide_adv_server = fields.Selection(Servidor().getServidores(), "EGA Server")
    pe_guide_adv_private_key = fields.Text("EGA Private key")
    pe_guide_adv_public_key = fields.Text("EGA Public key")
    pe_guide_report_template = fields.Selection([('standard', 'Standard'), ('custom', 'Custom'),('stylized','Stylized')], "Report Template", default='standard')