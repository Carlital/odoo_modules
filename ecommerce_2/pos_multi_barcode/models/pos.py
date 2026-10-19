# -*- coding: utf-8 -*-


from odoo import fields, models,tools,api
import json


class pos_multi_barcode(models.Model):
    _name = 'pos.multi.barcode'

    name = fields.Char('Barcode')
    product_id = fields.Many2one("product.product",string="Product")

    @api.model
    def _load_pos_data_domain(self, data):
        return []

    @api.model
    def _load_pos_data_fields(self):
        return ['name','product_id']

    def _load_pos_data(self, data):
        domain = self._load_pos_data_domain(data)
        fields = self._load_pos_data_fields()
        result = self.search_read(domain, fields, load=False)
        return {
            'data': result,
            'fields': fields,
        }

class product_product(models.Model):
    _inherit = 'product.product'

    pos_multi_barcode = fields.One2many('pos.multi.barcode','product_id',string='Barcodes')



    @api.model
    def _load_pos_data_fields(self, config_id):
        data = super()._load_pos_data_fields(config_id)
        data += ['pos_multi_barcode']
        return data

class PosSession(models.Model):
    _inherit = 'pos.session'


    @api.model
    def _load_pos_data_models(self, config_id):
        data = super()._load_pos_data_models(config_id)
        data += ['pos.multi.barcode']
        return data


    