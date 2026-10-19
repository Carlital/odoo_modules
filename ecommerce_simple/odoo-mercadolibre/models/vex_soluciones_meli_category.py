# models/meli_category.py
from odoo import models, fields

class MeliCategory(models.Model):
    _name = 'meli.category'
    _description = 'Categoría de MercadoLibre'

    name = fields.Char("Nombre")
    meli_id = fields.Char("ID ML", required=True)
    parent_id = fields.Many2one('meli.category', string="Categoría Padre")
    site_id = fields.Char("Site ID")
    full_path = fields.Char("Ruta completa")
    instance_id = fields.Many2one('vex.instance', string='instance')
    
    _sql_constraints = [
        ('unique_meli_id', 'unique(meli_id)', 'ID de categoría duplicado.'),
    ]
