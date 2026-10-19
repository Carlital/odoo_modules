
from odoo import api, fields, models


class HotelTour(models.Model):
    _name = 'hotel.tour'
    _description = "Hotel Tour"
    
    name = fields.Char('Nombre')
    street = fields.Char('Dirección')
    phone = fields.Char('Teléfono')
    country_id = fields.Many2one('res.country', 'País')

