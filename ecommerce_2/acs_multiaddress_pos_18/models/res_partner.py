# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    other = fields.Char(string='Otros')
    clientes_varios = fields.Boolean(string='Clientes Varios')

    def _load_pos_data_fields(self, config_id):
        """Especifica qué campos cargar en el POS"""
        result = super()._load_pos_data_fields(config_id)
        # Agregar campos personalizados
        result.extend(['other', 'clientes_varios', 'child_ids'])
        return result

    @api.model
    def create_from_ui(self, partner):
        extra_addrees = []
        if 'extra_addres' in partner:
            extra_addrees = partner.get('extra_addres', False)
            del partner['extra_addres']

        if partner.get('id'):
            partner_id = partner['id']
            partner_record = self.browse(partner_id)
            partner_vals = {k: v for k, v in partner.items() if k != 'id'}
            partner_record.write(partner_vals)
            res = partner_id
        else:
            res = super(ResPartner, self).create_from_ui(partner)

        if extra_addrees:
            for address in extra_addrees:
                self.env['res.partner'].create({
                    'type': 'invoice',
                    'parent_id': res,
                    'street': address.get('street', False),
                    'street2': address.get('street2', False),
                    'city': address.get('city', False),
                    'country_id': address.get('country_id', False),
                    'customer_rank': 0
                })
        return res
