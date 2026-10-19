from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    hide_col_discount = fields.Boolean(string='Ocultar columna descuento', default=False)
    hide_col_line_total = fields.Boolean(string='Ocultar columna total por linea', default=False)