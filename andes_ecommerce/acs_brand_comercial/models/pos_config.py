
from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    logotipo = fields.Binary(string='Logotipo',)
    brand_comercial_id = fields.Many2one('brand.comercial.tours','Marca comercial',)
    phone = fields.Char(string='Teléfono')
    email = fields.Char(string='Correo')
    address = fields.Char(string='Dirección')

    




    