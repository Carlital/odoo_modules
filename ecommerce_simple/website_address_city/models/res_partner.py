# -*- coding: utf-8 -*-
##########################################################################
# Author : Webkul Software Pvt. Ltd. (<https://webkul.com/>;)
# Copyright(c): 2017-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>;
##########################################################################
from odoo import models, fields
import logging
_log = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'
    def _prepare_display_address(self, without_company=False):
        res = super(ResPartner, self)._prepare_display_address(without_company=without_company)
        res[1]['city'] = self.city_id.name if self.country_id.enforce_cities and self.env['res.city'].search([('state_id','=',self.state_id.id)]) else self.city
        return res
