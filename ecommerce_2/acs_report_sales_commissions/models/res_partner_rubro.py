# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartnerRubro(models.Model):
    _name = 'res.partner.rubro'
    _description = 'Rubro Empresarial'
    _order = 'name'

    name = fields.Char(string='Nombre del Rubro', required=True)
    active = fields.Boolean(
        default=True, help="Desmarca esta casilla para ocultar el Rubro sin eliminarlo.")
