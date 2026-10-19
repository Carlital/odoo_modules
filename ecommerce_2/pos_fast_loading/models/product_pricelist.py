# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
#################################################################################
import json
import base64
from odoo import models, api, _
from odoo.http import request

import logging
_logger = logging.getLogger(__name__)

class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    def write(self, vals):
        vals_keys = vals.keys()
        change_vals = ','.join(vals_keys)
        if len(vals_keys):
            for record in self:
                record.create_price_operations(
                    record.id, 'UPDATE', change_vals)
        res = super(PricelistItem, self).write(vals)
        return res

    def create_price_operations(self, pl_item_id, operation, change_vals):
        active_configs = self.env['pos.config'].sudo().search(
            [('active', '=', True)])
        for config in active_configs:
            price_operations = self.env['common.cache.notification'].sudo().search([
                ('model_name', '=', "product.pricelist.item"),
                ('config_id', '=', config.id),
                ('record_id', '=', pl_item_id),
                ('state', 'in', ['error', 'draft']
                    )], order="id desc")

            if not (price_operations and price_operations[0].operation == 'UPDATE'):
                self.env['common.cache.notification'].sudo().create_pos_based_cache({
                    'record_id': pl_item_id,
                    'operation': 'UPDATE',
                    'model_name': "product.pricelist.item",
                    'change_vals': change_vals,
                    'state': 'draft'
                })

    @api.model_create_multi
    def create(self, vals):
        record = super(PricelistItem, self).create(vals)
        for rec in record:
            self.env['common.cache.notification'].create_pos_based_cache({
                'record_id': rec.id,
                'model_name': 'product.pricelist.item',
                'operation': "CREATE",
                'state': "draft",
                'change_vals': 'New Pricelist Item Created'
            })
        return record

    def unlink(self):
        for record in self:
            self.env['common.cache.notification'].create_pos_based_cache({
                'operation': "DELETE",
                'state': "draft",
                'model_name': 'product.pricelist.item',
                'record_id': record.id or False,
                'change_vals': 'Pricelist Item Deleted'
            })
        return super(PricelistItem, self).unlink()

    def _validate_pricelist_data(self, fields, mongo_server_rec):
        context = self._context
        is_indexed_updated = context.get('is_indexed_updated')

        if (context.get('sync_from_mongo')) and mongo_server_rec:
            request.session['pricelist_loaded_details'] = ''

            if is_indexed_updated and is_indexed_updated[0] and not is_indexed_updated[0].get('time') and mongo_server_rec.is_ordinary_loading and mongo_server_rec.is_updated:
                return []
            
            if mongo_server_rec.cache_last_update_time and mongo_server_rec.is_pos_data_synced:
                mongo_server_rec.is_ordinary_loading = False
                
                if mongo_server_rec.is_updated and is_indexed_updated and is_indexed_updated[0] and is_indexed_updated[0].get("time") \
                and is_indexed_updated[0].get("time") >= mongo_server_rec.cache_last_update_time.strftime("%Y-%m-%d %H:%M:%S"):
                    return []
                else:
                    return True
            else:
                return False

    def _load_pos_data(self, data):
        res = super(PricelistItem, self)._load_pos_data(data)
        fields = self._load_pos_data_fields(data['pos.config']['data'][0]['id'])

        try:
            mongo_server_rec = self.env['common.cache.notification'].get_active_mongo_config
            if mongo_server_rec:
                if mongo_server_rec.load_pos_data_from == "postgres":
                    # pricelists = self._validate_pricelist_data(fields, mongo_server_rec)
                    # Always return a dict, even if pricelists is empty
                    return {
                        'data': [],
                        'fields': fields,
                        'relations': {},   # ensure key exists to avoid NoneType error
                    }
                else:
                    return res
            else:
                # mongo_server_rec is False/None
                return res
        except Exception as e:
            _logger.error(f'Error in _load_pos_data: {e}')
            if self._context.get('sync_from_mongo'):
                context = self._context.copy()
                context.pop('sync_from_mongo', None)
                self = self.with_context(context)
            return res

