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
    _inherit = 'mongo.server.config'

    mongo_host = fields.Char(
        "Mongo Host",
        help="The hostname or IP address of the MongoDB server. Example: 127.0.0.1 or mongo.example.com"
    )
    mongo_port = fields.Integer(
        "Mongo Port",
        default=27017,
        help="The port number on which MongoDB is listening. Default is 27017."
    )
    is_port_available = fields.Boolean(
        "Is Port Available", 
        help="Enable this if the host field does not contains the port number.",
        default=True
        )
    mongo_user = fields.Char(
        "Mongo Username",
        help="The username used to authenticate with MongoDB. Leave empty if authentication is not enabled."
    )
    mongo_password = fields.Char(
        "Mongo Password",
        help="The password for the MongoDB user. Use a user with limited privileges for better security."
    )
    mongo_authdb = fields.Char(
        "Auth Database",
        default="admin",
        help="The database where the MongoDB user is created (authentication database). Usually 'admin'."
    )
    
    def check_connection(self):
        """
        Test MongoDB server connectivity.

        Sends a ping command to verify the MongoDB server is accessible.
        
        Returns
        -------
        dict
            Odoo UI notification action if connection is successful.

        Raises
        ------
        ValidationError
            If the connection fails or the MongoDB server is unreachable.
        """
        client = self.get_client()

        try:
            client.admin.command("ping")
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "type": "success",
                    "message": _("Connected successfully"),
                    "next": {"type": "ir.actions.act_window_close"},
                },
            }

        except Exception as e:
            _logger.error("MongoDB connection failed: %s", e)
            raise ValidationError(_("Connection failed: %s") % e)

    def get_client(self):
        """
        Build and return a MongoDB client instance.

        Returns
        -------
        MongoClient
            Configured client for connecting to the MongoDB server.

        Raises
        ------
        ValidationError
            If connection creation fails.
        """
        host = self.mongo_host or "localhost"
        port = self.mongo_port or 27017
        auth_db = self.mongo_authdb or "admin"

        username = urllib.parse.quote_plus(self.mongo_user or "")
        password = urllib.parse.quote_plus(self.mongo_password or "")

        # Build MongoDB URI
        if username:
            if self.is_port_available:
                uri = f"mongodb://{username}:{password}@{host}:{port}/{auth_db}"
            else:
                uri = f"mongodb://{username}:{password}@{host}/{auth_db}"
        else:
            uri = f"mongodb://{host}:{port}/{auth_db}" if self.is_port_available else f"mongodb://{host}/{auth_db}"

        try:
            return MongoClient(uri, serverSelectionTimeoutMS=5000)
        except Exception as e:
            raise ValidationError(f"Failed to initialize MongoDB client: {e}")

    @api.model
    def get_products_from_mongo(self, **kwargs):
        """
        Fetch product records stored in MongoDB for fast POS loading.

        Parameters
        ----------
        kwargs : dict
            Supported keys:
                - `offset` (int): Record offset used for pagination.
                - `fields` (list[str]): List of field names to fetch.
        
        Behavior
        --------
        Retrieves product data from the MongoDB `products` collection that
        is synced from Odoo. Supports pagination via `skip()` and `limit()`.
        If additional product fields are mapped in Odoo (`product_field_ids`),
        they are appended dynamically.

        Returns
        -------
        list[dict] | bool
            Returns a list of product dictionaries fetched from MongoDB.
            Each product dictionary contains only relevant fields and excludes the internal `_id`.
            Returns `False` if no MongoDB connection exists or an error occurs.
        """

        mongo_server_rec = self.env['common.cache.notification'].get_active_mongo_config

        if not mongo_server_rec:
            return False
            
        limit = mongo_server_rec.limit
        client = mongo_server_rec.get_client()

        try:
            if not client:
                return False

            database = self._cr.dbname

            if database not in client.list_database_names():
                return False
            
            PRODUCTFIELD = self.env['common.cache.notification'].get_product_fields
            fields = self.return_fields(mongo_server_rec, 'product.product', 'product_field_ids', PRODUCTFIELD, 'product_all_fields')

            products_col = client[database].products
            offset = kwargs.get('offset', 0)

            # ➤ Optimization: filter & projection only if fields exist
            projection = {field: 1 for field in fields} if fields else None

            cursor = products_col.find({}, projection).skip(offset).limit(limit)

            res = []
            for record in cursor:
                record.pop("_id", None)
                res.append(record)

            return res

        except Exception as e:
            _logger.error("Error fetching products from MongoDB: %r", e)
            return False

    @api.model
    def get_customers_from_mongo(self, **kwargs):
        """
        Retrieve only the 'server_data_cache' strings from MongoDB for the given company_id.
        Returns a list of strings.
        """

        mongo_server_rec = self.env["common.cache.notification"].get_active_mongo_config
        if not mongo_server_rec:
            return False

        given_company_id = kwargs.get("company_id")
        try:
            given_company_id = int(given_company_id)
        except Exception:
            given_company_id = None

        try:
            client = mongo_server_rec.get_client()
            database = self._cr.dbname

            if database not in client.list_database_names():
                return False

            db = client[database]
            partner_col = db.partners_batch

            cursor = partner_col.find()
            result_strings = []

            for rec in cursor:
                # Extract company_id from record
                rec_company = rec.get("company_id")
                if isinstance(rec_company, dict):
                    rec_company_id = rec_company.get("id")
                else:
                    rec_company_id = rec_company

                # Filter: company_id == given_company_id OR None
                if rec_company_id is None or rec_company_id == given_company_id:
                    server_cache = rec.get("server_data_cache")
                    if server_cache:
                        # Convert bytes to string if needed
                        if isinstance(server_cache, bytes):
                            server_cache = server_cache.decode('utf-8', errors='ignore')
                        result_strings.append(server_cache)
            return result_strings if result_strings else False

        except Exception as e:
            return False

    def sync_product_data_mongo(self, product_fields):
        try:
            mongo_server_rec = self.env['common.cache.notification'].get_active_mongo_config
            if not mongo_server_rec:
                return 0

            client = mongo_server_rec.get_client()
            database = self._cr.dbname

            # Fetch products
            products = self.env['product.product'].sudo().search(
                [('sale_ok', '=', True), ('available_in_pos', '=', True)]
            )
            count = len(products)

            db = client[database]
            db.products.drop()
            products_col = db.products

            # Process in batches (1000 -> 100)
            for batch1000 in range(math.ceil(count / 1000)):
                batch_products = products[batch1000 * 1000:(batch1000 + 1) * 1000]

                # List to insert for this batch only
                product_data = []

                for batch100 in range(math.ceil(len(batch_products) / 100)):
                    recs = batch_products[batch100 * 100:(batch100 + 1) * 100]
                    pro_data = recs.read(product_fields, load=False)

                    if pro_data:
                        product_data.extend(pro_data)

                if product_data:
                    products_col.insert_many(product_data)

            return count

        except ServerSelectionTimeoutError:
            raise ValidationError("server is down.")


    def sync_partner_data_mongo(self, partner_fields):
        mongo_server_rec = self.env['common.cache.notification'].get_active_mongo_config

        if mongo_server_rec:
            partners = self.env['res.partner'].search([])
            count = len(partners)

            client = mongo_server_rec.get_client()
            databases = client.list_database_names()
            database = self._cr.dbname

            if database in databases:
                db = client[database]
                db.partners.drop()
                partners_col = db.partners

                for count in range(math.ceil(len(partners)/1000)):
                    partners_data = []
                    data_to_add = partners[count*1000:(count+1)*1000]
                    for record in range(math.ceil(len(data_to_add)/100)):
                        data_to_find = data_to_add[record *
                                                   100:(record+1)*100]
                        pro_data = data_to_find.read(partner_fields)
                        if len(pro_data):
                            partners_data.extend(pro_data)
                    partners_col.insert_many(partners_data)
                partners_synced = len(partners)
            else:
                db = client[database]
                partners_col = db.partners
                for count in range(math.ceil(len(partners)/1000)):
                    partners_data = []
                    data_to_add = partners[count*1000:(count+1)*1000]
                    for record in range(math.ceil(len(data_to_add)/100)):
                        data_to_find = data_to_add[record *
                                                   100:(record+1)*100]
                        pro_data = data_to_find.read(partner_fields)
                        if len(pro_data):
                            partners_data.extend(pro_data)
                    partners_col.insert_many(partners_data)

            return count

    
