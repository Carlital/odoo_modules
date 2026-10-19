# -*- coding: utf-8 -*-

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    x_is_commission_agent = fields.Boolean(
        string='Vendedor comisionista',
        help="Marque esta casilla si este usuario es un vendedor que participa en el cálculo de comisiones."
    )
