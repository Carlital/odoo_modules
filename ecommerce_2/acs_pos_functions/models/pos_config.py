
from odoo import api, fields, models

class PosConfig(models.Model):
    _inherit = 'pos.config'

    disable_ctrl_p = fields.Boolean(string="Deshabilitar CTRL+P")
    disable_right_click = fields.Boolean(string="Deshabilitar click derecho")