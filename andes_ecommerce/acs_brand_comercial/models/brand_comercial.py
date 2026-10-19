
import os
import base64

from odoo import fields, models, tools


class BrandComercialTours(models.Model):
    _name = 'brand.comercial.tours'
    _description = 'Brand Comercial Tours'
    _order = 'name'

    def _get_logo(self):
        return base64.b64encode(
            open(os.path.join(
                tools.config['root_path'],
                'addons',
                'base',
                'static',
                'img',
                'res_company_logo.png'), 'rb') .read())

    name = fields.Char('Nombre', required=True)
    logo = fields.Binary(default=_get_logo, string="Logo")
    email = fields.Char('Correo electronico')
    phone = fields.Char('Telefono')
    mobile = fields.Char('Movil')
    website = fields.Char('Sitio web')

    reason = fields.Char('Razon Social')
    rut = fields.Char('RUT')
    street = fields.Char('Dirección')

    custom_template_mail_sale_id = fields.Many2one(
        string='Plantilla de correo para Ventas',
        comodel_name='mail.template', domain=[('model', '=', 'sale.order'), ])
    custom_template_mail_invoice_id = fields.Many2one(
        string='Plantilla de correo para Facturación',
        comodel_name='mail.template',
        domain=[('model', '=', 'account.move'), ])
