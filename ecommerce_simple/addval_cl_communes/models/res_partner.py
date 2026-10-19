# -*- encoding: utf-8 -*-
from odoo import fields, models, api
from odoo.tools.translate import _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.depends('city_id')
    def _give_city_name(self):
        for record in self:
            if record.city_id:
                record.zip = self.city_id.zipcode
                record.state_id = self.city_id.state_id
                record.city = self.city_id.name
            else:
                record.zip = False
                record.state_id = False
                record.city = ""

