from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    
    sign_request_mail = fields.Char(
        string="Correo electrónico para Solicitudes de Firma", 
        config_parameter='addval_sign_extension.sign_request_mail'
    )
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            sign_request_mail =self.env['ir.config_parameter'].sudo().get_param('addval_sign_extension.sign_request_mail')
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('addval_sign_extension.sign_request_mail', self.sign_request_mail )