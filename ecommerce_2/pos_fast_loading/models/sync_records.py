# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################
from odoo import fields, models
import logging
_logger = logging.getLogger(__name__)

class ModelDataRecord(models.Model):
    _name = 'model.data.record'
    _description = "Model Data Record"

    model_name = fields.Selection(
        [('product.product', 'Product'), ('res.partner', 'Partner')], string='Model Name')
    mongo_config = fields.Many2one(
        string='Mongo Config', comodel_name='mongo.server.config', ondelete='restrict')
    server_data_cache = fields.Binary(string="Server Data Cache")
    min_id = fields.Integer("Min Id")
    max_id = fields.Integer("Max Id")
    offset_start = fields.Integer("Offset Start")
    offset_end = fields.Integer("Offset end")
    company_id = fields.Many2one(
        'res.company', string='Company', readonly=False)
    

class PosFastLoadingMessage(models.TransientModel):
    _name = "pos.fast.loading.message"
    _description = "Pos Fast Loading Message"

    text = fields.Text('Message')
