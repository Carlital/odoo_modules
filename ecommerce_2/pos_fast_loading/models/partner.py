# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################
import json
import base64
import logging
from odoo.http import request
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    def mongo_server_validation(self, is_indexed_updated, mongo_server_rec_read, load_pos_data_type=''):
        if load_pos_data_type:
            return mongo_server_rec_read.get('is_updated') and is_indexed_updated and is_indexed_updated[0] and is_indexed_updated[0].get("time") and is_indexed_updated[0].get("time") >= mongo_server_rec_read.get('cache_last_update_time').strftime("%Y-%m-%d %H:%M:%S")

        return len(is_indexed_updated) and not is_indexed_updated[0].get('time') and mongo_server_rec_read.get('is_ordinary_loading') and mongo_server_rec_read.get('is_updated')

    def _fetch_data_from_db(self, load_pos_data_type, mongo_server_rec, mongo_server_rec_read, reloaded_flag, company_id):
        context = self._context

        match load_pos_data_type:
            case 'mongo':
                # Through MongoDB
                data = self.env['mongo.server.config'].get_customers_from_mongo(fields=fields, company_id=company_id)
                if data:
                    return data
            case 'postgres':
                # Through postgres
                # ****************decode data************************
                if reloaded_flag is False and mongo_server_rec_read.get('pos_live_sync') == 'reload':
                    self.env['common.cache.notification'].get_common_changes()

                binary_data_rec = mongo_server_rec.collection_data.filtered(
                    lambda x: x.model_name == 'res.partner' and (x.company_id.id == False or x.company_id.id == company_id.id)
                )
                if binary_data_rec:
                    if not request.session['partner_loaded_details']:
                        request.session['partner_loaded_details'] = ','.join(str(rec.id) for rec in binary_data_rec)
                    return [rec.server_data_cache for rec in binary_data_rec]

    def _load_pos_data(self, data):
        try:
            reloaded_flag = False
            mongo_server_rec = self.env['common.cache.notification'].get_active_mongo_config
            fields = self._load_pos_data_fields(data['pos.config']['data'][0]['id'])
            config = self.env['pos.config'].browse(data['pos.config']['data'][0]['id'])
            mongo_server_rec_read = mongo_server_rec.read(['collection_data', 'load_pos_data_from', 'cache_last_update_time', 'is_pos_data_synced', 'pos_live_sync', 'is_updated'])
            mongo_server_rec_read = mongo_server_rec_read[0] if mongo_server_rec_read else mongo_server_rec_read
            is_indexed_updated = self._context.get('is_indexed_updated', [])
            sync_from_mongo = self._context.get('sync_from_mongo', False)
        
            if sync_from_mongo and mongo_server_rec:
                request.session['partner_loaded_details'] = ''
                load_pos_data_type = mongo_server_rec_read.get('load_pos_data_from')

                if mongo_server_rec_read.get('cache_last_update_time') and mongo_server_rec_read.get('is_pos_data_synced'):
                    mongo_server_rec.is_ordinary_loading = False
                    if mongo_server_rec_read.get('pos_live_sync') == 'reload' and not mongo_server_rec_read.get('is_ordinary_loading'):
                        # Need to fetch all changes on reload
                        # 1. Reload
                        # 2. Real-time
                        # 3. Through Button
                        self.env['common.cache.notification'].get_common_changes()
                        reloaded_flag = True

                    # if self.mongo_server_validation(is_indexed_updated, mongo_server_rec_read, load_pos_data_type) and load_pos_data_type == "mongo":
                    #     return []

                    batches = self._fetch_data_from_db(load_pos_data_type, mongo_server_rec, mongo_server_rec_read, reloaded_flag, config.company_id)
                    if batches:
                        return {
                            'data': batches,
                            'fields': fields,
                        }
                    else:
                        return super(ResPartner, self)._load_pos_data(data)
                else:
                    mongo_server_rec.is_ordinary_loading = True
                    return super(ResPartner, self)._load_pos_data(data)
        except Exception as e:
            return super(ResPartner, self)._load_pos_data(data)
        return super(ResPartner, self)._load_pos_data(data)

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        vals_keys = set(vals.keys())
        change_vals = ','.join(vals_keys)
        fields = set(['name', 'street', 'city', 'state_id', 'country_id', 'vat', 'phone', 'zip',
                     'mobile', 'email', 'barcode', 'write_date', 'property_account_position_id', 'active'])
        common_fields = fields.intersection(vals_keys)
        if len(common_fields):
            for record in self:
                active_configs = self.env['pos.config'].sudo().search(
                    [('active', '=', True)])
                for config in active_configs:
                    partner_operations = self.env['common.cache.notification'].sudo().search([
                        ('model_name', '=', "res.partner"),
                        ('config_id', '=', config.id),
                        ('record_id', '=', record.id),
                        ('state', 'in', ['error', 'draft']
                         )], order="id desc")

                    if not (partner_operations and partner_operations[0].operation == 'UPDATE'):
                        self.env['common.cache.notification'].sudo().create_pos_based_cache({
                            'record_id': record.id,
                            'operation': 'UPDATE',
                            'model_name': "res.partner",
                            'change_vals': change_vals,
                            'state': 'draft'
                        })
        return res

    @api.model_create_multi
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        for rec in res:
            if rec:
                self.env['common.cache.notification'].sudo().create_pos_based_cache({
                    'record_id': rec.id,
                    'operation': 'CREATE',
                    'model_name': "res.partner",
                    'change_vals': 'New Partner Created',
                    'state': 'draft'
                })
        return res

    def unlink(self):
        for record in self:
            self.env['common.cache.notification'].sudo().create_pos_based_cache({
                'record_id': record.id,
                'operation': 'DELETE',
                'model_name': "res.partner",
                'change_vals': 'Partner Deleted',
                'state': 'draft'
            })
        return super(ResPartner, self).unlink()
