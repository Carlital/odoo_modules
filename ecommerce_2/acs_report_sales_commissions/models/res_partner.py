# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    rubro_ids = fields.Many2many(
        'res.partner.rubro',
        string='Rubros',
        help='Seleccione los rubros empresariales de este contacto.'
    )
