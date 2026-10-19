# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from librecpe import Servidor
from odoo.exceptions import ValidationError

class PeCpeWizard(models.TransientModel):
    _name = "pe.eguide.advanced.wizard"
    _description = "CPE Wizard"

    pe_guide_adv_ws_url = fields.Char("Guide Web Service URL")
    pe_guide_adv_user = fields.Char("EGA User")
    pe_guide_adv_password = fields.Char("EGA Password/Token")
    pe_guide_adv_client_id = fields.Char("EGA Client Id")
    pe_guide_adv_client_secret = fields.Char("EGA Client Secret")
    pe_guide_adv_verify_url = fields.Char("EGA Eguide Verify Url", default="https://e-factura.sunat.gob.pe/")
    pe_guide_adv_server = fields.Selection(Servidor().getServidores(), "EGA Server", required=True)
    pe_guide_adv_private_key = fields.Text("EGA Private key")
    pe_guide_adv_public_key = fields.Text("EGA Public key")

    company_id = fields.Many2one(comodel_name='res.company', string='Company', required = True,
                                 readonly=True)


    @api.model
    def default_get(self, fields_list):
        values = super(PeCpeWizard, self).default_get(fields_list)
        if self.env.context['active_model'] == 'res.config.settings' and 'active_ids' in self.env.context:
            active_settings_ids = self.env['res.config.settings'].browse(self.env.context['active_ids'])
            company_id = active_settings_ids and active_settings_ids[0].company_id or False
            values['pe_guide_adv_ws_url'] = company_id and company_id.pe_guide_adv_ws_url or False
            values['pe_guide_adv_user'] = company_id and company_id.pe_guide_adv_user or False
            values['pe_guide_adv_password'] = company_id and company_id.pe_guide_adv_password or False
            values['pe_guide_adv_client_id'] = company_id and company_id.pe_guide_adv_client_id or False
            values['pe_guide_adv_client_secret'] = company_id and company_id.pe_guide_adv_client_secret or False
            values['pe_guide_adv_verify_url'] = company_id and company_id.pe_guide_adv_verify_url or False
            values['pe_guide_adv_server'] = company_id and company_id.pe_guide_adv_server or False
            values['pe_guide_adv_private_key'] = company_id and company_id.pe_guide_adv_private_key or False
            values['pe_guide_adv_public_key'] = company_id and company_id.pe_guide_adv_public_key or False
            values['company_id'] = company_id and company_id.id or False
        return values
    
    @api.onchange('pe_guide_adv_server')
    def onchange_pe_guide_adv_server(self):
        self.ensure_one()
        vals = {}
        if self.pe_guide_adv_server in ['nubefact_ose', 'otros']:
            vals['warning'] = {
                'title': _('Warning!'),
                'message': _("You can't use this server, please select another one")
            }
        return vals

    def appy_configuration(self):
        self.ensure_one()
        if self.pe_guide_adv_server in ['nubefact_ose', 'otros']:
            raise ValidationError(_("You can't use this server, please select another one"))
        values = {}
        values['pe_guide_adv_ws_url'] = self.pe_guide_adv_ws_url or False
        values['pe_guide_adv_user'] = self.pe_guide_adv_user or False
        values['pe_guide_adv_password'] = self.pe_guide_adv_password or False
        values['pe_guide_adv_client_id'] = self.pe_guide_adv_client_id or False
        values['pe_guide_adv_client_secret'] = self.pe_guide_adv_client_secret or False
        values['pe_guide_adv_verify_url'] = self.pe_guide_adv_verify_url or False
        values['pe_guide_adv_server'] = self.pe_guide_adv_server or False
        values['pe_guide_adv_private_key'] = self.pe_guide_adv_private_key or False
        values['pe_guide_adv_public_key'] = self.pe_guide_adv_public_key or False
        self.company_id.write(values)
    