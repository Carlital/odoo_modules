# models/meli_option.py
from odoo import models, fields

class MeliOption(models.Model):
    _name = 'meli.option'
    _description = 'Opciones de MercadoLibre'

    name = fields.Char(string="Nombre")
    code = fields.Char(string="Código (id ML)")
    field_name = fields.Selection([
        ('listing_type', 'Tipo de Publicación'),
        ('condition', 'Condición'),
        ('buying_mode', 'Modo de Compra'),
    ], required=True)
    site_id = fields.Char(string="Site ID", required=True)
    active = fields.Boolean(default=True)
    instance_id = fields.Many2one('vex.instance', string='instance')
    
    _sql_constraints = [
        ('unique_option_code', 'unique(code, field_name, site_id)', 'Ya existe esta opción.'),
    ]
