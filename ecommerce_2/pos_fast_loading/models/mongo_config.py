# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################
import math
import zlib
import json
import base64
import urllib.parse
from odoo.http import request
from datetime import datetime
from odoo.tools import json_default
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

try:
    from pymongo import MongoClient
    from pymongo.errors import ServerSelectionTimeoutError
except Exception as e:
    _logger.info("Python's PyMongo Library is not installed. \
                 Please run below command to install it \
                 pip3 install -r pos_fast_loading/requirements.txt")


class MongoServerConfig(models.Model):
    _name = 'mongo.server.config'
    _description = "Mongo Server Config"
    _rec_name = 'load_pos_data_from'

    active_record = fields.Boolean(default=False, readonly=True)
    product_field_ids = fields.Many2many('ir.model.fields', 'product_mapping_with_mongo', string="Additional Product Fields",
                                         domain="[('model_id.model','=','product.product'),('name','not in',['display_name', 'list_price', 'lst_price', 'standard_price', 'categ_id', 'pos_categ_ids', 'taxes_id','barcode', 'default_code', 'to_weight', 'uom_id', 'description_sale', 'description','product_tmpl_id','tracking'])]")
    partner_field_ids = fields.Many2many('ir.model.fields', 'customer_mapping_with_mongo', string="Additional Partner Fields",
                                         domain="[('model_id.model','=','res.partner'),('name','not in',['name','street','city','state_id','country_id','vat','phone','zip','mobile','email','barcode','write_date','property_account_position_id','property_product_pricelist'])]")

    collection_data = fields.One2many(
        string='Loaded Record', comodel_name='model.data.record', inverse_name='mongo_config',)
    limit = fields.Integer(
        'Limit', default=1000, help="Limit to load the first time records. Remaining will load in the background")

    product_last_update_time = fields.Datetime('Product Last Sync Time')
    cache_last_update_time = fields.Datetime('Cache Last Sync Time')
    price_last_update_time = fields.Datetime('Price Last Sync Time')
    partner_last_update_time = fields.Datetime('Customer Last Sync Time')

    is_updated = fields.Boolean("Is updated", default=False)
    partner_all_fields = fields.Boolean('All Partner Fields', default=False)
    product_all_fields = fields.Boolean('All Products Fields', default=False)

    is_product_synced = fields.Boolean('Is Product Synced', default=False)
    is_partner_synced = fields.Boolean('Is Partner Synced', default=False)
    is_pricelist_synced = fields.Boolean('Is Pricelist Synced', default=True)

    pos_pricelist_cache = fields.Binary(string="Pos Pricelist Cache")

    is_ordinary_loading = fields.Boolean(
        string="Is Loaded Ordinary", default=False)
    is_pos_data_synced = fields.Boolean(
        string="Is All Data Synced", default=False)

    load_pos_data_from = fields.Selection(string="Load Pos Data From", selection=[
                                          ('postgres', 'Postgres'), ('mongo', 'Mongo')], default="postgres")
    pos_live_sync = fields.Selection(string="Pos Syncing", selection=[('realtime', 'Real Time Update'), (
        'notify', 'Only notify when Changes Occur'), ('reload', 'Apply changes on reloading')], default="notify")

    # Fields for sync using cron
    sync_from_cron = fields.Boolean(
        string="Sync from Cron",
        default=False,
        help="Enable this to sync data using cron jobs automatically. Buttons will be hidden when enabled."
    )
    partner_sync_in_progress = fields.Boolean(default=False)
    partner_sync_offset = fields.Integer(default=0)
    partner_sync_total = fields.Integer(default=0)
    partner_sync_company_index = fields.Integer(default=0)
    product_sync_in_progress = fields.Boolean(default=False)
    product_sync_offset = fields.Integer(default=0)
    product_sync_total = fields.Integer(default=0)
    product_sync_company_index = fields.Integer(default=0)
    records_sync_cron_id = fields.Many2one(
        'ir.cron',
        string="Sync Cron",
        readonly=True,
        help="Cron job used for Sync Product and Partners record"
    )

    def return_fields(self, mongo_server_rec, model_name, custom_field_ids, fields, all_fields_include):
        fields = fields.copy()
        fields_list = getattr(mongo_server_rec, custom_field_ids)
        if fields_list:
            fields = fields + [str(data.name)
                               for data in fields_list]
        if getattr(mongo_server_rec, all_fields_include):
            if mongo_server_rec.load_pos_data_from == 'postgres':
                model_fields = self.env['ir.model.fields'].sudo().search_read(
                    [('model', '=', model_name), ('ttype', 'not in', ['binary', 'properties', 'properties_definition'])], ['name'])
                new_fields = [i['name'] for i in model_fields]
                temp_fields = set(fields).union(set(new_fields))
                fields = list(temp_fields)
            else:
                fields = []
        return fields

    def delete_server_cache(self, model_name, mongo_server_rec):
        server_rec = self.env['model.data.record'].search(
            [('mongo_config', '=', mongo_server_rec.id), ('model_name', '=', model_name)])
        if len(server_rec):
            server_rec.unlink()

    def toggle_active_record(self):
        self.active_record = not self.active_record

    @api.constrains('active_record')
    def validate_mongo_server_active_records(self):
        records = self.search([])
        count = 0
        for record in records:
            if record.active_record == True:
                count += 1
        if (count > 1):
            raise ValidationError("You can't have two active mongo configs.")

    def delete_common_cache(self, model_name):
        records_to_delete = self.env['common.cache.notification'].search(
            [('model_name', '=', model_name)])
        if len(records_to_delete):
            records_to_delete.unlink()

    def _load_pos_data(self, data):
        domain = [('active_record', '=', True)]
        fields = ['cache_last_update_time',
                  'pos_live_sync', 'active_record', 'limit']
        data = self.search_read(domain, fields, load=False, limit=1)

        return {
            'data': data,
            'fields': fields,
        }

    # If click on sync button in pos then call this method
    @api.model
    def get_data_on_sync(self, **kwargs):
        config_id = kwargs.get('config_id', False)
        pos_mongo_config = kwargs.get('mongo_cache_last_update_time')

        if config_id:
            config_id = self.env['pos.config'].browse(kwargs.get('config_id'))

        mongo_server_rec = self.env['common.cache.notification'].get_active_mongo_config
        if mongo_server_rec:
            product_data = []
            pricelist_item_data = []
            data_dict = {
                'products': [],
                'pricelist_items': [],
                'partners': [],
                'price_deleted_record_ids': [],
                'partner_deleted_record_ids': [],
                'product_deleted_record_ids': [],
                'mongo_config': mongo_server_rec.cache_last_update_time,
                'sync_method': mongo_server_rec.pos_live_sync
            }
            try:
                new_cache_records = self.env['common.cache.notification'].search(
                    [('state', '!=', 'done'), ('config_id', '=', config_id.id)])
                uid = kwargs.get('context', {}).get('uid')
                user = self.env['res.users'].sudo().browse(uid)
                self.env['common.cache.notification'].with_context(
                    coming_from_pos=True, user=user).with_user(uid).get_common_changes(config_id)

                if new_cache_records:
                    product_record_ids = []
                    price_record_ids = []
                    partner_record_ids = []
                    partner_deleted_record_ids = []
                    price_deleted_record_ids = []
                    product_deleted_record_ids = []
                    price_res = []
                    product_res = []
                    partner_res = []
                    for record in new_cache_records:
                        if record.model_name == 'product.product':
                            if record.operation == 'DELETE':
                                product_deleted_record_ids.append(
                                    record.record_id)
                            else:
                                product_record_ids.append(record.record_id)
                        elif record.model_name == 'res.partner':
                            if record.operation == 'DELETE':
                                partner_deleted_record_ids.append(
                                    record.record_id)
                            else:
                                partner_record_ids.append(record.record_id)
                        elif record.model_name == 'product.pricelist.item':
                            if record.operation == 'DELETE':
                                price_deleted_record_ids.append(
                                    record.record_id)
                            elif record.operation == 'UPDATE':
                                price_record_ids.append(record.record_id)
                                # price_deleted_record_ids.append(record.record_id)
                            else:
                                price_record_ids.append(record.record_id)

                    load_pos_data_type = mongo_server_rec.load_pos_data_from
                    if load_pos_data_type == 'mongo':
                        client = mongo_server_rec.get_client()
                        if client:
                            database = self._cr.dbname
                            if database in client.list_database_names():
                                db = client[database]
                                if len(price_record_ids):
                                    pricelist_items_col = db.pricelist_items
                                    pricelist_item_data = pricelist_items_col.find(
                                        {'id': {'$in': price_record_ids}})
                                    for record in pricelist_item_data:
                                        if record.get('id'):
                                            if (record.get('_id')):
                                                del record['_id']
                                            price_res.append(record)
                                    pricelist_item_deleted_data = pricelist_items_col.find(
                                        {'id': {'$in': price_deleted_record_ids}})
                                if len(product_record_ids):
                                    products_col = db.products
                                    product_data = products_col.find(
                                        {'id': {'$in': product_record_ids}})
                                    for record in product_data:
                                        if record.get('id'):
                                            if (record.get('_id')):
                                                del record['_id']
                                            product_res.append(record)
                                if len(partner_record_ids):
                                    partners_col = db.partners
                                    partner_data = partners_col.find(
                                        {'id': {'$in': partner_record_ids}})
                                    for record in partner_data:
                                        if record.get('id'):
                                            if (record.get('_id')):
                                                del record['_id']
                                            partner_res.append(record)
                    else:
                        if len(price_record_ids):
                            binary_data = mongo_server_rec.pos_pricelist_cache
                            json_data = json.loads(
                                base64.decodebytes(binary_data).decode('utf-8'))
                            for obj in json_data:
                                if int(obj) in price_record_ids:
                                    price_res.append(json_data.get(obj))

                        if len(product_record_ids) and config_id:
                            product_res = self.env['product.product'].with_user(
                                self.env.context['uid']).with_company(
                                config_id.company_id.id).search([('id', 'in', product_record_ids)])
                            PRODUCTFIELD = self.env['common.cache.notification'].get_product_fields
                            pro_fields = self.return_fields(
                                mongo_server_rec, 'product.product', 'product_field_ids', PRODUCTFIELD, 'product_all_fields')

                            product_res = product_res.read(
                                pro_fields, load=False)

                        if len(partner_record_ids) and config_id:
                            PARTNERFIELD = self.env['common.cache.notification'].with_context(
                                user=user).with_user(uid).get_partner_fields
                            partner_res = self.env['res.partner'].with_user(self.env.context['uid']).with_company(
                                config_id.company_id.id).search_read([('id', 'in', partner_record_ids)], fields=self.return_fields(mongo_server_rec, 'res.partner', 'partner_field_ids', PARTNERFIELD, 'partner_all_fields'))

                    self.env['product.product']._process_pos_ui_product_product(
                        product_res, config_id)

                    data_dict.update({
                        'products': product_res,
                        'pricelist_items': price_res,
                        'partners': partner_res,
                        'mongo_config': mongo_server_rec.cache_last_update_time,
                        'price_deleted_record_ids': price_deleted_record_ids,
                        'partner_deleted_record_ids': partner_deleted_record_ids,
                        'product_deleted_record_ids': product_deleted_record_ids
                    })
                    new_cache_records.write({'state': 'done'})
                return data_dict
            except Exception as e:
                return data_dict

    def write(self, vals):
        for obj in self:
            if obj.load_pos_data_from != vals.get('load_pos_data_from') and vals.get('load_pos_data_from'):
                vals.update({
                    'product_last_update_time': False,
                    'cache_last_update_time': False,
                    'price_last_update_time': False,
                    'partner_last_update_time': False,
                    'is_ordinary_loading': True,
                    'is_product_synced': False,
                    'is_pricelist_synced': True,
                    'is_partner_synced': False
                })
        res = super(MongoServerConfig, self).write(vals)
        return res

    def find_related_product_file(self, product_id, create=False):
        if self.collection_data:
            if create:
                bin_file_data = self.collection_data.filtered(
                    lambda x: x.model_name == 'product.product' and x.min_id <= product_id and x.offset_end <= self.limit)
            else:
                bin_file_data = self.collection_data.filtered(
                    lambda x: x.model_name == 'product.product' and x.min_id <= product_id and x.max_id >= product_id)
            if bin_file_data:
                return bin_file_data[0]
            else:
                return False
        else:
            return False

    def find_related_partner_file(self, partner_id, create=False):
        if self.collection_data:
            if create:
                bin_file_data = self.collection_data.filtered(
                    lambda x: x.model_name == 'res.partner' and x.min_id <= partner_id and x.offset_end <= self.limit)
            else:
                bin_file_data = self.collection_data.filtered(
                    lambda x: x.model_name == 'res.partner' and x.min_id <= partner_id and x.max_id >= partner_id)
            if bin_file_data:
                return bin_file_data[0]
            else:
                return False
        else:
            return False

    def load_rem_product(self, page, company_id, session_id, offset):
        mongo_server_rec = self.env['common.cache.notification'].get_active_mongo_config
        res = {
            'raw_count': 0,
            'products': [],
        }

        if not mongo_server_rec:
            return res

        if mongo_server_rec.load_pos_data_from == 'postgres':
            temp = request.session.get('product_loaded_details', '')
            col_ids = [int(i) for i in temp.split(',') if i.isdigit()]

            binary_data_rec = mongo_server_rec.collection_data.filtered(
                lambda x: x.model_name == 'product.product'
                and x.id not in col_ids
                and (not x.company_id.id or x.company_id.id == company_id)
            )

            raw_data = False
            if binary_data_rec and len(binary_data_rec) > 1:
                temp += str(binary_data_rec[0].id) + ','
                raw_data = binary_data_rec[0].server_data_cache

            if not raw_data:
                _logger.warning("Empty cache*******************")
                return []

            try:
                decoded = base64.decodebytes(raw_data)
                decoded_str = decoded.decode('utf-8')
                json_data = json.loads(decoded_str)
            except Exception as e:
                _logger.exception(
                    "Error decoding product cache ID %s: %s", binary_data_rec[0].id, e)
                return []

            products = list(json_data.values())
            request.session['product_loaded_details'] = temp

            raw_count = bool(len(products))
            if products:
                session = self.env['pos.session'].browse(session_id)
                products = session.config_id.filter_products_by_config_categories(
                    products)
                self.env['product.product']._process_pos_ui_product_product(
                    products, session.config_id)

            res['raw_count'] = raw_count
            res['products'] = products
        else:
            products = self.get_products_from_mongo(offset=offset)
            res['raw_count'] = len(products)
            res['products'] = products or []

        return {
            'raw_count': len(products),
            'products': products,
        }

    def load_rem_customer(self, **kw):
        mongo_server_rec = self.env['common.cache.notification'].get_active_mongo_config
        partners = []
        if mongo_server_rec:
            offset = kw.get('offset') or 0
            _logger.info(
                f"####### loading remaining customers offset - {offset} ############")
            if mongo_server_rec and mongo_server_rec.load_pos_data_from == 'mongo':
                partners = mongo_server_rec.get_customers_from_mongo(
                    offset=offset)
            else:
                _logger.info("####### remaining partner loaded ############")

        return partners

    def load_product_data_postgres(self, p_data, product_fields, company):
        products_data = {}
        product_dict = {}
        pro_data = p_data.read(product_fields, load=False)
        # self.env['product.product']._process_pos_ui_product_product(pro_data, company)
        for product_conv_data in pro_data:
            product_dict[product_conv_data.get('id')] = product_conv_data
            products_data.update(product_dict)
        return products_data

    def create_partners_batch(self, mongo_server_rec, partner_fields):
        companies = self.env['res.company'].search([('active', '=', True)])
        ids = [None]
        ids.extend(companies.ids)
        data = {}
        for company_id in ids:
            offset = 0
            full_data = {}
            batch_size = 10000

            comp_id = company_id
            if not company_id:
                comp_id = 0
                data[0] = {}
            else:
                data[company_id] = {}

            if not company_id:
                self._cr.execute(
                    'SELECT COUNT(*) FROM res_partner WHERE active = TRUE AND company_id IS NULL')
            else:
                self._cr.execute(
                    'SELECT COUNT(*) FROM res_partner WHERE active = TRUE AND company_id = %s', (company_id,))

            total_count = self._cr.fetchone()[0]

            while offset < total_count:
                domain = [('active', '=', True)]
                if company_id:
                    domain.append(('company_id', '=', company_id))
                else:
                    domain.append(('company_id', '=', False))

                partners = self.env['res.partner'].sudo().search(
                    domain, offset=offset, limit=batch_size)

                if not partners:
                    break

                partner_batch = partners.read(partner_fields, load=False)

                full_data.update(
                    {str(rec['id']): rec for rec in partner_batch})

                offset += batch_size

                _logger.info(
                    f"[Partner Sync] Loaded {len(partner_batch)} records for company={company_id} (offset: {offset})")

            if not full_data:
                data[comp_id]['count'] = 0
                continue

            partner_ids = list(map(int, full_data.keys()))
            min_id = min(partner_ids)
            max_id = max(partner_ids)

            # Zlib compression
            compressed_data = base64.encodebytes(
                zlib.compress(json.dumps(
                    full_data, default=json_default).encode('utf-8'))
            )

            data[comp_id] = {
                'count': total_count,
                'server_data_cache': compressed_data,
                'mongo_config': mongo_server_rec.id,
                'offset_start': 0,
                'offset_end': total_count,
                'min_id': min_id,
                'max_id': max_id,
                'model_name': 'res.partner',
                'company_id': company_id if company_id else None,
            }

        return data

    def sync_partners(self):
        server_data_batch = self.env['model.data.record']
        mongo_server_rec = self

        if not mongo_server_rec.active_record:
            raise ValidationError("Please activate Mongo config first.")

        recs = []
        count = 0
        load_type = mongo_server_rec.load_pos_data_from

        self.delete_server_cache('res.partner', mongo_server_rec)

        PARTNERFIELD = self.env['common.cache.notification'].get_partner_fields
        partner_fields = self.return_fields(
            mongo_server_rec, 'res.partner', 'partner_field_ids', PARTNERFIELD, 'partner_all_fields'
        )

        data = self.create_partners_batch(mongo_server_rec, partner_fields)

        if load_type == 'mongo':
            client = mongo_server_rec.get_client()
            databases = client.list_database_names()
            database = self._cr.dbname

            # Get or create database
            db = client[database] if database in databases else client[database]

            # Drop old collection
            if 'partners_batch' in db.list_collection_names():
                db.partners_batch.drop()

            partners_batch_col = db.partners_batch

            # Insert each company batch in Mongo
            total_sync_count = 0
            for company_id, batch in data.items():
                batch_copy = dict(batch)     # Do not mutate original dict
                batch_count = batch_copy.pop('count', 0)

                total_sync_count += batch_count

                # Insert the batch as a single document in MongoDB
                partners_batch_col.insert_one({
                    'company_id': company_id if company_id != 0 else None,
                    'mongo_config': mongo_server_rec.id,
                    'offset_start': batch_copy.get('offset_start'),
                    'offset_end': batch_copy.get('offset_end'),
                    'min_id': batch_copy.get('min_id'),
                    'max_id': batch_copy.get('max_id'),
                    'model_name': "res.partner",
                    'server_data_cache': batch_copy.get('server_data_cache'),
                    'created_at': datetime.now(),
                })

            count = total_sync_count

        else:

            for key, value in data.items():
                count += value.get('count')
                value.pop('count', None)
                batch_rec = server_data_batch.create(value)
                self._cr.commit()
                recs.extend([batch_rec.id])

            if recs:
                mongo_server_rec.collection_data = [(4, 0, recs)]

        mongo_server_rec.write({
            'partner_last_update_time': datetime.now(),
            'is_partner_synced': True
        })

        self.delete_common_cache('res.partner')

        try:
            if mongo_server_rec.is_partner_synced and mongo_server_rec.is_product_synced:
                mongo_server_rec.write({
                    'is_ordinary_loading': False,
                    'is_pos_data_synced': True,
                    'cache_last_update_time': datetime.now(),
                })

            msg = self.env['pos.fast.loading.message'].create({
                'text': f"{count} Customers have been synced."
            })
            return {
                'name': _("Message"),
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'pos.fast.loading.message',
                'res_id': msg.id,
                'type': 'ir.actions.act_window',
                'target': 'new',
            }
        except Exception as e:
            _logger.exception("Error during partner sync: %s", e)

    def create_product_batch(self, mongo_server_rec, server_data_batch, product_fields, company=None):
        offset = 0
        limit = mongo_server_rec.limit
        recs = []

        company_filter = f"= {company.id}" if company else "IS NULL"

        self._cr.execute(f"""
            SELECT COUNT(*)
            FROM product_product pp
            INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
            WHERE pp.active = TRUE
            AND pt.available_in_pos = TRUE
            AND pt.sale_ok = TRUE
            AND pt.company_id {company_filter}
        """)
        total_products = self._cr.fetchone()[0]

        while offset < total_products:
            self._cr.execute(f"""
                SELECT pp.id
                FROM product_product pp
                INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id
                WHERE pp.active = TRUE
                AND pt.available_in_pos = TRUE
                AND pt.sale_ok = TRUE
                AND pt.company_id {company_filter}
                ORDER BY pp.id
                OFFSET {offset}
                LIMIT {limit}
            """)
            product_keys = [row[0] for row in self._cr.fetchall()]

            if not product_keys:
                break

            variant_data = self.env['product.product'].sudo().browse(product_keys)
            products_data = self.sudo().load_product_data_postgres(variant_data, product_fields, company)
            min_id = min(product_keys)
            max_id = max(product_keys)

            temp = offset + len(product_keys)

            batch_data = {
                'server_data_cache': base64.encodebytes(json.dumps(products_data, default=json_default).encode('utf-8')),
                'mongo_config': mongo_server_rec.id,
                'offset_start': offset,
                'min_id': min_id,
                'max_id': max_id,
                'offset_end': temp,
                'model_name': 'product.product',
                'company_id': company.id if company else None,
            }
            batch_rec = server_data_batch.create(batch_data)
            recs.append(batch_rec.id)

            offset = temp
            self._cr.commit()

        return {
            'count': total_products,
            'recs': recs,
        }

    def sync_products(self):
        server_data_batch = self.env['model.data.record']
        mongo_server_rec = self.env['common.cache.notification'].get_active_mongo_config

        if not mongo_server_rec:
            raise ValidationError("Please activate a Mongo config first.")

        count = 0
        batches = []
        load_pos_data_type = mongo_server_rec.load_pos_data_from

        self.delete_server_cache('product.product', mongo_server_rec)
        PRODUCTFIELD = self.env['common.cache.notification'].get_product_fields
        product_fields = self.return_fields(
            mongo_server_rec, 'product.product', 'product_field_ids', PRODUCTFIELD, 'product_all_fields')

        if load_pos_data_type == 'mongo':
            count = self.sync_product_data_mongo(product_fields)
        else:
            res = self.create_product_batch(mongo_server_rec, server_data_batch, product_fields)
            count += res['count']        
            batches.extend(res['recs'])
            active_companies = self.env['res.company'].sudo().search([('active', '=', True)])
    
            for company in active_companies:
                res = self.create_product_batch(
                    mongo_server_rec, server_data_batch, product_fields, company=company)
                count += res['count']
                batches.extend(res['recs'])

            if batches:
                mongo_server_rec.collection_data = [(4, 0, batches)]

        now = fields.Datetime.now()
        mongo_server_rec.write({
            'product_last_update_time': now,
            'is_product_synced': True,
        })

        self.delete_common_cache('product.product')

        try:
            if all([mongo_server_rec.is_partner_synced, mongo_server_rec.is_pricelist_synced, mongo_server_rec.is_product_synced]):
                mongo_server_rec.write({
                    'is_ordinary_loading': False,
                    'is_pos_data_synced': True,
                    'cache_last_update_time': now,
                })

            message = self.env['pos.fast.loading.message'].create(
                {'text': f"{count} Products have been synced."})
            return {
                'name': _("Message"),
                'view_mode': 'form',
                'res_model': 'pos.fast.loading.message',
                'res_id': message.id,
                'type': 'ir.actions.act_window',
                'target': 'new',
            }
        except Exception as e:
            _logger.error("Exception during product sync: %s", e)

    def reset_config(self):
            self.write({
                'product_last_update_time': False,
                'cache_last_update_time': False,
                'price_last_update_time': False,
                'partner_last_update_time': False,
                "is_partner_synced": False,
                "is_pos_data_synced": False,
                "is_pricelist_synced": True,
                "is_product_synced": False,
                'partner_sync_in_progress': False,
                'partner_sync_offset': 0,
                'partner_sync_total': 0,
                'partner_sync_company_index': 0,
                'product_sync_in_progress': False,
                'product_sync_offset': 0,
                'product_sync_total': 0,
                'product_sync_company_index': 0,
            })

            self.delete_server_cache('product.product', self)
            self.delete_server_cache('res.partner', self)
            self.delete_server_cache('product.pricelist.item', self)

    def cron_sync_records(self):
        configs = self.search([('active_record', '=', True), ('sync_from_cron', '=', True)])
        
        for mongo_server_rec in configs:
            if not mongo_server_rec:
                continue

            if not mongo_server_rec.is_product_synced:
                if not mongo_server_rec.product_sync_in_progress:
                    mongo_server_rec.write({
                        'product_sync_offset': 0,
                        'product_sync_total': 0,
                        'product_sync_company_index': 0,
                        'product_sync_in_progress': True,
                    })
                    mongo_server_rec.delete_server_cache('product.product', mongo_server_rec)
                
                mongo_server_rec.cron_sync_products()
                mongo_server_rec._cr.commit()
                continue

            # Partner Sync Block
            if not mongo_server_rec.is_partner_synced:
                if not mongo_server_rec.partner_sync_in_progress:
                    mongo_server_rec.write({
                        'partner_sync_offset': 0,
                        'partner_sync_total': 0,
                        'partner_sync_company_index': 0,
                        'partner_sync_in_progress': True,
                    })
                    mongo_server_rec.delete_server_cache('res.partner', mongo_server_rec)
                
                mongo_server_rec.cron_sync_partners()
                mongo_server_rec._cr.commit()
                continue
        

    # def cron_sync_products(self):
    #     offset = self.product_sync_offset or 0
    #     company_index = self.product_sync_company_index or 0
    #     total_synced = self.product_sync_total or 0
    #     _logger.info("---------------------[Product Sync] Start. Index: %s, Offset: %s, Total so far: %s", company_index, offset, total_synced)

    #     companies = self.env['res.company'].search([('active', '=', True)])
    #     company_ids = [None] + companies.ids
    #     _logger.debug("---------------------[Product Sync] Target Company IDs: %s", company_ids)

    #     if not company_ids or company_index >= len(company_ids):
    #         _logger.info("---------------------[Product Sync] No more companies or index out of range. Finalizing.")
    #         self._finalize_product_sync(total_synced)
    #         return

    #     company_id = company_ids[company_index]
    #     company = self.env['res.company'].browse(company_id) if company_id else None
    #     _logger.info("---------------------[Product Sync] Processing Company: %s", company.name if company else "Global/No Company")

    #     server_data_batch = self.env['model.data.record']
    #     product_fields = self.return_fields(
    #         self, 'product.product', 'product_field_ids',
    #         self.env['common.cache.notification'].get_product_fields,
    #         'product_all_fields'
    #     )

    #     batch_size = self.limit or 1000
    #     max_compressed_count = 200000
    #     compressed_count = 0
    #     full_data = {}

    #     _logger.info("---------------------[Product Sync] Starting batch fetching loop. Batch size: %s", batch_size)
    #     _logger.info(f'-----------------compressed_count----------------------------{compressed_count}')
    #     _logger.info(f'-----------------max_compressed_count----------------------------{max_compressed_count}')

    #     while compressed_count < max_compressed_count:
    #         _logger.info(f'=====================inside**while==================================')
    #         products = self._fetch_records_batch(offset, batch_size, company, product_fields, 'product.product')

    #         if not products:
    #             _logger.info("---------------------[Product Sync] No more records found for this company in current batch.")
    #             break

    #         _logger.debug("---------------------[Product Sync] Fetched %s records.", len(products))
    #         full_data.update({str(rec['id']): rec for rec in products})
    #         compressed_count += len(products)
    #         offset += batch_size

    #     if full_data:
    #         _logger.info("---------------------[Product Sync] Preparing to save %s records to cache table.", len(full_data))
    #         product_ids = list(map(int, full_data.keys()))
    #         min_id, max_id = min(product_ids), max(product_ids)

    #         compressed_data = base64.encodebytes(json.dumps(
    #             full_data, default=json_default).encode('utf-8'))

    #         server_data_batch.create({
    #             'server_data_cache': compressed_data,
    #             'mongo_config': self.id,
    #             'offset_start': offset - compressed_count,
    #             'offset_end': offset,
    #             'min_id': min_id,
    #             'max_id': max_id,
    #             'model_name': 'product.product',
    #             'company_id': company.id if company else None,
    #         })
    #         self._cr.commit()
    #         total_synced += compressed_count
    #         _logger.info("---------------------[Product Sync] Batch committed. Total synced: %s", total_synced)

    #     if compressed_count < max_compressed_count:
    #         _logger.info("---------------------[Product Sync] Company finished. Moving to next company index.")
    #         company_index += 1
    #         offset = 0

    #     self.write({
    #         'product_sync_offset': offset,
    #         'product_sync_company_index': company_index,
    #         'product_sync_total': total_synced
    #     })

    def cron_sync_products(self):
        offset = int(self.product_sync_offset or 0)
        company_index = int(self.product_sync_company_index or 0)
        total_synced = int(self.product_sync_total or 0)
        companies = self.env['res.company'].search([('active', '=', True)])
        company_ids = [None] + companies.ids

        if not company_ids or company_index >= len(company_ids):
            self._finalize_product_sync(total_synced)
            return

        company_id = company_ids[company_index]
        company = self.env['res.company'].browse(company_id) if company_id else None

        server_data_batch = self.env['model.data.record']
        product_fields = self.return_fields(
            self, 'product.product', 'product_field_ids',
            self.env['common.cache.notification'].get_product_fields,
            'product_all_fields'
        )

        batch_size = int(self.limit or 1000)
        max_compressed_count = 200000
        compressed_count = 0

        # Loop fetching and persisting each batch immediately to avoid building one huge payload
        while True:
            products = self._fetch_records_batch(offset, batch_size, company, product_fields, 'product.product')

            if not products:
                break

            # Build small dict for this batch only
            try:
                batch_data = {str(rec['id']): rec for rec in products}
            except Exception:
                # Fallback: ensure we don't crash if a record is malformed
                batch_data = {}
                for rec in products:
                    if 'id' in rec:
                        batch_data[str(rec['id'])] = rec

            product_ids = list(map(int, batch_data.keys())) if batch_data else []
            if product_ids:
                min_id, max_id = min(product_ids), max(product_ids)
            else:
                min_id = max_id = None

            # Compress and store this batch
            compressed_data = base64.b64encode(json.dumps(batch_data, default=json_default).encode('utf-8'))

            server_data_batch.create({
                'server_data_cache': compressed_data,
                'mongo_config': self.id,
                'offset_start': offset,
                'offset_end': offset + len(products),
                'min_id': min_id,
                'max_id': max_id,
                'model_name': 'product.product',
                'company_id': company.id if company else None,
            })
            # Commit after each batch to keep transactions small and durable
            try:
                self._cr.commit()
            except Exception:
                # If commit fails, log and continue (or re-raise depending on desired behavior)
                raise

            compressed_count += len(products)
            total_synced += len(products)

            # Advance offset by actual number of returned records (safer than adding batch_size)
            offset += len(products)

            # Stop if we've reached an overall safety cap for this run
            if compressed_count >= max_compressed_count:
                break

        # If we finished the company (i.e., didn't hit the cap), move to next company
        if compressed_count < max_compressed_count:
            company_index += 1
            offset = 0

        # Persist progress
        self.write({
            'product_sync_offset': offset,
            'product_sync_company_index': company_index,
            'product_sync_total': total_synced
        })

    def cron_sync_partners(self):
        offset = self.partner_sync_offset or 0
        company_index = self.partner_sync_company_index or 0
        total_synced = self.partner_sync_total or 0
        companies = self.env['res.company'].search([('active', '=', True)])
        company_ids = [None] + companies.ids

        if not company_ids or company_index >= len(company_ids):
            self._finalize_partner_sync(total_synced)
            return

        company_id = company_ids[company_index]
        company = self.env['res.company'].browse(company_id) if company_id else None

        server_data_batch = self.env['model.data.record']
        partner_fields = self.return_fields(
            self, 'res.partner', 'partner_field_ids',
            self.env['common.cache.notification'].get_partner_fields,
            'partner_all_fields'
        )

        batch_size = 10000
        max_compressed_count = 200000

        compressed_count = 0
        full_data = {}

        while compressed_count < max_compressed_count:
            partners = self._fetch_records_batch(offset, batch_size, company, partner_fields, 'res.partner')
            if not partners:
                break

            full_data.update({str(rec['id']): rec for rec in partners})
            compressed_count += len(partners)
            offset += batch_size

        if full_data:
            partner_ids = list(map(int, full_data.keys()))
            min_id, max_id = min(partner_ids), max(partner_ids)

            compressed_data = base64.encodebytes(
                zlib.compress(json.dumps(full_data, default=json_default).encode('utf-8'))
            )

            server_data_batch.create({
                'server_data_cache': compressed_data,
                'mongo_config': self.id,
                'offset_start': offset - compressed_count,
                'offset_end': offset,
                'min_id': min_id,
                'max_id': max_id,
                'model_name': 'res.partner',
                'company_id': company.id if company else None,
            })
            self._cr.commit()
            total_synced += compressed_count
            _logger.info(
                f"[Partner Sync] Compressed {compressed_count} records (total: {total_synced}) for company={company and company.name} (offset: {offset})")

        if compressed_count < max_compressed_count:
            company_index += 1
            offset = 0

        self.write({
            'partner_sync_offset': offset,
            'partner_sync_company_index': company_index,
            'partner_sync_total': total_synced
        })

    def _fetch_records_batch(self, offset, limit, company, fields, model):
        domain = [('active', '=', True)]
        if company:
            domain.append(('company_id', '=', company.id))
        else:
            domain.append(('company_id', '=', False))

        if model == 'product.product':
            domain.extend([('sale_ok', '=', True), ('available_in_pos', '=', True)])

        records = self.env[model].with_context(prefetch_fields=False).sudo().search(domain, offset=offset, limit=limit)
        res = records.read(fields, load=False)
        return res

    def _finalize_partner_sync(self, total_synced):
            self.write({
                'partner_last_update_time': datetime.now(),
                'is_partner_synced': True,
                'partner_sync_offset': 0,
                'partner_sync_company_index': 0,
                'partner_sync_total': 0,
                'partner_sync_in_progress': False,
            })

            if self.is_product_synced:
                self.write({
                    'is_ordinary_loading': False,
                    'is_pos_data_synced': True,
                    'cache_last_update_time': datetime.now(),
                })
            # return self._get_sync_message(f"{total_synced} Customers have been synced.")

    def _finalize_product_sync(self, total_synced):
            self.write({
                'product_last_update_time': datetime.now(),
                'is_product_synced': True,
                'product_sync_in_progress': False,
                # Note: The original code didn't reset offset/total here, but it's good practice
                'product_sync_offset': 0, 
                'product_sync_company_index': 0,
                'product_sync_total': 0,
            })

            if self.is_partner_synced:
                self.write({
                    'is_ordinary_loading': False,
                    'is_pos_data_synced': True,
                    'cache_last_update_time': datetime.now(),
                })
            # return self._get_sync_message(f"{total_synced} products have been synced.")

    @api.onchange('sync_from_cron', 'active_record')
    def assign_sync_cron(self):
        cron = self.env.ref(
            "pos_fast_loading.cron_records_sync", raise_if_not_found=False)
        if cron:
            configs = self.search([("sync_from_cron", "=", True)])
            configs.write({"records_sync_cron_id": cron.id})
            

""" Flow========================
 When click on sync hit in pos ==> "get_data_on_sync" method
"""
