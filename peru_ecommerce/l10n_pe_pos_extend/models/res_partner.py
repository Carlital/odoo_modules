# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
import requests
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create_from_ui(self, partner):
        partner_data = partner.get('id', False)
        if partner_data:
            partner_id = self.browse(partner_data)
            if partner_id and partner_id.id == self.env.ref('l10n_pe_pos.partner_pe_cf').id:
                raise ValidationError(_('Cannot modify the final consumer partner'))
        if not partner.get('l10n_latam_identification_type_id') and partner.get('vat'):
            partner['vat'] = False

        res = super(ResPartner, self).create_from_ui(partner)
        return res
