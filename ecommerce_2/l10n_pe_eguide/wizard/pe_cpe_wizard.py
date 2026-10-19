# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from librecpe import Servidor


class PeCpeWizard(models.TransientModel):
    _inherit = "pe.cpe.wizard"

    pe_guide_ws_url = fields.Char("Guide Web Service URL", required = True)
    pe_guide_user = fields.Char("Guide User")
    pe_guide_password = fields.Char("Guide Password", required = True)
    pe_guide_client_id = fields.Char("Client Id")
    pe_guide_client_secret = fields.Char("Client Secret")
    pe_eguide_verify_url = fields.Char("Eguide Verify Url", default="https://e-factura.sunat.gob.pe/")

    @api.model
    def default_get(self, fields_list):
        values = super(PeCpeWizard, self).default_get(fields_list)
        if self.env.context['active_model'] == 'res.config.settings' and 'active_ids' in self.env.context:
            active_settings_ids = self.env['res.config.settings'].browse(self.env.context['active_ids'])
            company_id = active_settings_ids and active_settings_ids[0].company_id or False
            values['pe_guide_ws_url'] = company_id and company_id.pe_guide_ws_url or False
            values['pe_guide_user'] = company_id and company_id.pe_guide_user or False
            values['pe_guide_password'] = company_id and company_id.pe_guide_password or False
            values['pe_guide_client_id'] = company_id and company_id.pe_guide_client_id or False
            values['pe_guide_client_secret'] = company_id and company_id.pe_guide_client_secret or False
            values['pe_eguide_verify_url'] = company_id and company_id.pe_eguide_verify_url or False
        return values
    
    
    def appy_configuration(self):
        self.ensure_one()
        res = super(PeCpeWizard, self).appy_configuration()
        values = {}
        values['pe_guide_ws_url'] = self.pe_guide_ws_url or False
        values['pe_guide_user'] = self.pe_guide_user or False
        values['pe_guide_password'] = self.pe_guide_password or False
        values['pe_guide_client_id'] = self.pe_guide_client_id or False
        values['pe_guide_client_secret'] = self.pe_guide_client_secret or False
        values['pe_eguide_verify_url'] = self.pe_eguide_verify_url or False
        self.company_id.write(values)
        return res
    