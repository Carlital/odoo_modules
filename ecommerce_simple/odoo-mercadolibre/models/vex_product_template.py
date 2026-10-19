# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import json
from dateutil.parser import isoparse
import base64
import logging
_logger = logging.getLogger(__name__)
import datetime
from datetime import datetime, timedelta

from prophet import Prophet
import pandas as pd
import numpy as np

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    meli_json_data = fields.Text(string="MercadoLibre JSON", help="Full JSON response from MercadoLibre")
    meli_product_id = fields.Char(string="ML Product ID", help="MercadoLibre product identifier")
    meli_site_id = fields.Char(string="ML Site ID", help="MercadoLibre site identifier")
    meli_title = fields.Char(string="ML Title", help="Title of the product on MercadoLibre")
    meli_family_name = fields.Char(string="Family Name", help="Product family name if any")
    meli_seller_id = fields.Char(string="Seller ID", help="Identifier of the seller on MercadoLibre")
    meli_user_product_id = fields.Char(string="User Product ID", help="User product reference if available")
    meli_official_store_id = fields.Char(string="Official Store ID", help="Official store ID if listed under a store")
    meli_price = fields.Float(string="Price", help="Selling price on MercadoLibre")
    meli_base_price = fields.Float(string="Base Price", help="Original base price")
    meli_original_price = fields.Float(string="Original Price", help="Original listed price if different from base")
    meli_currency_id = fields.Char(string="Currency", help="Currency used for pricing")
    meli_initial_quantity = fields.Integer(string="Initial Quantity", help="Quantity at time of listing")
    meli_available_quantity = fields.Integer(string="Available Quantity", help="Units currently available")
    meli_sold_quantity = fields.Integer(string="Sold Quantity", help="Total units sold")
    meli_buying_mode = fields.Selection(
        [
            ('buy_it_now', 'Compra inmediata'),
        ],
        string="Modo de compra",
        required=True,
        help="Modo de compra permitido por Mercado Libre"
    )
    meli_listing_type = fields.Selection(
        [
            ('gold_pro', 'Premium'),
            ('gold_special', 'Clásica'),
        ],
        string="Tipo de publicación",
        help="Tipo de publicación en Mercado Libre"
    )
    meli_condition = fields.Selection(
        [
            ('new', 'Nuevo'),
            ('used', 'Usado'),
            ('not_specified', 'No especificado'),
        ],
        string="Condición ML"
    )
    meli_permalink = fields.Char(string="Product URL", help="Permanent link to the product on MercadoLibre")
    meli_thumbnail = fields.Char(string="Thumbnail URL", help="URL of the product thumbnail")
    meli_inventory_id = fields.Char(string="Inventory ID", help="Inventory identifier in MercadoLibre")
    meli_category_vex = fields.Char(string="ML Category ID", help="MercadoLibre category identifier")
    meli_category_id = fields.Many2one(
        'product.category',  # Cambia por el modelo correcto si usas otro
        string="ML Category",
        help="MercadoLibre category identifier"
    )
    meli_catalog_product_id = fields.Char(string="Catalog Product ID", help="Catalog product reference from MercadoLibre")
    meli_domain_id = fields.Char(string="Domain ID", help="Domain classification of the product")
    meli_start_time = fields.Datetime(string="Start Time", help="Start date of listing")
    meli_stop_time = fields.Datetime(string="Stop Time", help="End date of listing")
    meli_end_time = fields.Datetime(string="End Time", help="Final date of listing")
    meli_expiration_time = fields.Datetime(string="Expiration Time", help="Expiration date of listing")
    meli_last_updated = fields.Datetime(string="Last Updated", help="Date of last update")
    meli_accepts_mp = fields.Boolean(string="Accepts MercadoPago", help="Whether MercadoPago is accepted")
    meli_shipping_mode = fields.Char(string="Shipping Mode", help="Shipping mode used (e.g., me2)")
    meli_free_shipping = fields.Boolean(string="Free Shipping", help="Indicates if the item has free shipping")
    meli_store_pick_up = fields.Boolean(string="Store Pickup", help="Indicates if store pickup is allowed")
    meli_local_pick_up = fields.Boolean(string="Local Pickup", help="Indicates if local pickup is allowed")
    meli_shipping_tags = fields.Char(string="Shipping Tags", help="Tags related to shipping features")
    meli_tag_ids = fields.Many2many(
        'product.meli.tag',
        'product_template_meli_tag_rel',
        'product_tmpl_id',
        'tag_id',
        string='ML Tags'
    )

    meli_channel_ids = fields.Many2many(
        'product.meli.channel',
        'product_template_meli_channel_rel',
        'product_tmpl_id',
        'channel_id',
        string='ML Channels'
    )

    meli_status = fields.Char(string="ML Status", help="Product status on MercadoLibre")
    meli_sub_status = fields.Char(string="Substatus", help="List of sub-statuses such as out_of_stock")
    meli_health = fields.Float(string="Health Score", help="Health score indicator of the product listing")

    meli_geolocation_lat = fields.Float(string="Latitude", help="Product geolocation latitude")
    meli_geolocation_lng = fields.Float(string="Longitude", help="Product geolocation longitude")
    meli_address_line = fields.Char(string="Address", help="Address line of the seller")
    meli_zip_code = fields.Char(string="ZIP Code", help="ZIP Code from seller address")
    meli_seller_city = fields.Char(string="Seller City", help="City name of the seller")
    meli_seller_state = fields.Char(string="Seller State", help="State name of the seller")
    meli_seller_country = fields.Char(string="Seller Country", help="Country name of the seller")

    meli_pictures_ids = fields.One2many('product.template.meli.image', 'product_tmpl_id', string="ML Pictures")
    meli_variation_ids = fields.One2many('product.template.meli.variation', 'product_tmpl_id', string="ML Variations")
    meli_attribute_ids = fields.One2many('product.template.meli.attribute', 'product_tmpl_id', string="ML Attributes")

    performance_score_ids = fields.One2many("product.performance.score", 'product_tmpl_id', string="Puntajes de rendimiento")
    meli_actual_price = fields.Float(string="Current Price", help="Current price of the product on MercadoLibre")
    meli_campaign_id = fields.Char(string="ML Campaign ID", help="ID of the campaign if applicable")
    meli_promotion_id = fields.Char(string="ML Promotion ID", help="ID of the promotion if applicable")
    meli_promotion_type = fields.Char(string="ML Promotion Type", help="Type of promotion applied to the product")
    meli_item_market_fee = fields.Float(
        string="Marketplace Fee",
        help="Calculated marketplace fee for the product based on its price, listing type, and category"
    )
    evolution_data_ids = fields.One2many(
        'vex.soluciones.price.evolution.data', 'product_id', string='Price Evolution Data'
    )
    meli_type_item_logistc = fields.Selection(
        [('fulfillment', 'Fulfillment'), ('not_fulfillment', 'Not Fulfillment')],
        string='Type Item Logistic',
        help="Type of logistic used for the item, either Fulfillment or Not Fulfillment",
        default='not_fulfillment',
        compute='_compute_meli_type_item_logistc'
        )

    competitor_price_history_ids = fields.One2many(
        'mercado.libre.product.compared',
        compute='_compute_competitor_price_history',
        string="Historial de Precios de la Competencia",
        store=False  # Solo visualización
    )

    recommended_price = fields.Float(string='Recommended Price')
    meli_question_ids = fields.One2many('vex.meli.questions', 'product_id', string="Questions")
    ready_create = fields.Boolean(string="Listo para Crear",compute="_compute_ready_create", store=True)
    meli_warranty_type = fields.Selection([
        ('2230280', 'Garantia de Proveedor'),
    ], string="Tipo de Garantía")
    meli_warranty_time = fields.Char(string="Tiempo de Garantía (días)", help="Duración de la garantía en días")
    meli_description = fields.Text(string="Descripción en MercadoLibre")
    meli_logistic_type = fields.Selection([
        ("fulfillment", "Fulfillment (Mercado Libre Full)"),
        ("cross_docking", "Cross Docking"),
        ("drop_off", "Drop Off (Sucursal de correo)"),
        ("xd_drop_off", "Cross Docking + Drop Off"),
        ("self_service", "Self Service (Logística propia)"),
        ("not_specified", "No especificado"),
    ],
        default="not_specified",
        string="Tipo de logística",
        required=True,
        help="""
        fulfillment: El producto está en los almacenes de Mercado Libre (Full).
        cross_docking: El vendedor lleva la mercadería a una estación de Mercado Libre y desde ahí se despacha.
        drop_off: El vendedor despacha el producto en una sucursal de correo autorizado por ML.
        xd_drop_off: Variante mixta: drop off + cross docking.
        self_service: El vendedor organiza y paga su propia logística.
        not_specified: No se especifica ningún tipo de logística.
        """
    )
    meli_stock_location_id = fields.Many2one(
        'stock.location',
        string="Ubicación ML",
        help="Ubicación de stock usada para sincronizar con Mercado Libre"
    )

    @api.depends(
        'meli_title', 'meli_category_vex', 'meli_currency_id', 'meli_available_quantity',
        'meli_buying_mode', 'meli_condition', 'meli_listing_type', 'meli_base_price',
        'meli_thumbnail', 'meli_pictures_ids', 'meli_attribute_ids'
    )
    def _compute_ready_create(self):
        for rec in self:
            # Validar campos simples
            campos_ok = all([
                rec.meli_title,
                rec.meli_listing_type,
                rec.meli_condition,
                rec.meli_description,
                rec.meli_category_vex,
                rec.meli_buying_mode,
                rec.meli_available_quantity,
                rec.meli_currency_id,
                rec.meli_thumbnail,
                rec.meli_warranty_type,
                rec.meli_warranty_time,
            ])
            # Validar imágenes secundarias (al menos una)
            imagenes_ok = bool(rec.meli_pictures_ids)
            # Validar atributos (al menos uno y que estén completos)
            atributos_ok = any(
                attr.meli_attribute_ref_id and (attr.meli_values_id or attr.meli_value_name)
                for attr in rec.meli_attribute_ids
            )
            rec.ready_create = campos_ok and imagenes_ok and atributos_ok

    def _compute_meli_type_item_logistc(self):
        """
        Compute the type of logistic used for the item based on the logistic type.
        If the logistic type is 'fulfillment', set meli_type_item_logistc to 'fulfillment'.
        Otherwise, set it to 'not_fulfillment'.
        """
        for record in self:
            if record.meli_logistic_type == 'fulfillment':
                record.meli_type_item_logistc = 'fulfillment'
            else:
                record.meli_type_item_logistc = 'not_fulfillment'
                
    def safe_parse_date(self,value):
        try:
            dt = isoparse(value) if value else False
            return dt.replace(tzinfo=None) if dt else False
        except Exception:
            return False
    # headers button for this product


    def _compute_competitor_price_history(self):
        for product in self:
            ml_products = self.env['mercado.libre.product'].search([
                ('product', '=', product.id)
            ])
            compared = self.env['mercado.libre.product.compared'].search([
                ('parent_id', 'in', ml_products.ids)
            ])
            product.competitor_price_history_ids = compared

    def action_update_stock(self):
        self.ensure_one()
        return {
            'name': 'Update Stock ML',
            'type': 'ir.actions.act_window',
            'res_model': 'product.meli.update.stock',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.id,
            }
        }

    def action_update_price(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'update.meli.price.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.id,
            }
        }
    
    def action_sync_questions(self):
        "Sincronizar preguntas con MercadoLibre para este producto mediante la API."
        for record in self:
            if not record.meli_product_id:
                raise UserError("Debe establecer primero el campo ML Product ID.")
            if not record.instance_id or not record.instance_id.meli_access_token:
                raise UserError("No se ha definido el token de acceso en la instancia vinculada.")
            
            access_token = record.instance_id.meli_access_token

            url = f"https://api.mercadolibre.com/questions/search?item_id={record.meli_product_id}"
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                raise UserError(f"Error al consultar API de MercadoLibre: {response.status_code} - {response.text}")
            
            data = response.json()
            questions = data.get('questions', [])
            _logger.info(f"Preguntas recibidas: {len(questions)}")
            if not questions:
                raise UserError("No hay preguntas para este producto en MercadoLibre.")
            QuestionsModel = self.env['vex.meli.questions']

            for q in questions:
                vals = {
                    'name': q.get('text', 'Pregunta'),
                    'meli_created_at': self.safe_parse_date(q.get('date_created')),
                    'meli_item_id': q.get('item_id'),
                    'meli_seller_id': q.get('seller_id'),
                    'meli_status': q.get('status'),
                    'meli_text': q.get('text'),
                    'meli_id': str(q.get('id')),
                    'meli_deleted_from_listing': q.get('deleted_from_listing', False),
                    'meli_hold': q.get('hold', False),
                    'meli_answer': q.get('answer', {}).get('text') if q.get('answer') else False,
                    'meli_from_id': str(q.get('from', {}).get('id')) if q.get('from') else False,
                    'meli_from_nickname': q.get('from', {}).get('nickname') if q.get('from') else False,
                    'meli_answered_at': self.safe_parse_date(q.get('answer', {}).get('date_created')) if q.get('answer') else False,
                    'meli_instance_id': record.instance_id.id,
                    'product_id': record.id,
                }
                existing_question = QuestionsModel.search([('meli_id', '=', vals['meli_id'])], limit=1)
                if existing_question:
                    existing_question.write(vals)
                else:
                    QuestionsModel.create(vals)
                    _logger.info(f"Pregunta creada: {vals}")

    def action_get_price(self):
        for record in self:
            if not record.meli_product_id:
                raise UserError("Debe establecer primero el campo ML Product ID.")
            access_token = record.instance_id and record.instance_id.meli_access_token
            if not access_token:
                raise UserError("No se ha definido el token de acceso en la instancia vinculada.")
            url = f"https://api.mercadolibre.com/items/{record.meli_product_id}/sale_price?context=channel_marketplace,buyer_loyalty_3"
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                raise UserError(f"Error al consultar API de MercadoLibre: {response.status_code} - {response.text}")
            data = response.json()
            old_price = record.meli_actual_price
            new_price = data.get('amount', 0.0)
            record.meli_item_market_fee = self._get_marketplace_fee(
                headers,
                new_price,
                record.meli_listing_type,
                record.meli_category_vex,
                record.instance_id.id
            )
            if old_price != new_price:
                record.meli_actual_price = data.get('amount', 0.0)
                metadata = data.get('metadata', {}) or {}
                record.meli_campaign_id = metadata.get('campaign_id', '')
                record.meli_promotion_id = metadata.get('promotion_id', '')
                record.meli_promotion_type = metadata.get('promotion_type', '')
                obj_history_price = {
                    'change_date': fields.Datetime.now(),
                    'old_price': old_price,
                    'new_price': new_price,
                }
                list_history = []
                list_history.append((0,0,obj_history_price))
                _logger.info(f"Actualizando precio de producto {record.name} de {old_price} a {new_price}")
                _logger.info(f"list_history: {list_history}")
                record.write({
                    'evolution_data_ids': list_history,
                })

    def action_publish_product(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'vex.publish.product.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id},
        }

    def action_get_details(self):
        """
        Fetches product details from MercadoLibre API and updates the product template.
        Also processes tags, channels, pictures, attributes, variations, and marketplace info.
        """
        instance = self.instance_id
        instance.get_access_token()
        for record in self:
            if not record.meli_product_id:
                raise UserError("Debe establecer primero el campo ML Product ID.")

            access_token = instance.meli_access_token
            if not access_token:
                raise UserError("No se ha definido el token de acceso en la instancia vinculada.")

            url = f"https://api.mercadolibre.com/items/{record.meli_product_id}?include_attributes=all"
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                raise UserError(f"Error al consultar API de MercadoLibre: {response.status_code} - {response.text}")

            data = response.json()
            record.meli_json_data = json.dumps(data,indent=4, ensure_ascii=False)

            # Referencias a modelos de apoyo
            Tag = record.env['product.meli.tag']
            Channel = record.env['product.meli.channel']
            Marketplace = record.env['vex.marketplace']
            Picture = record.env['product.template.meli.image']
            Attribute = record.env['product.template.meli.attribute']
            Variant = record.env['product.template.meli.variation']

            # Procesar tags
            tag_ids = []
            for tag in data.get('tags', []):
                tag_rec = Tag.search([('name', '=', tag)], limit=1)
                if not tag_rec:
                    tag_rec = Tag.create({'name': tag})
                tag_ids.append(tag_rec.id)

            # Procesar canales
            channel_ids = []
            for channel in data.get('channels', []):
                ch_rec = Channel.search([('name', '=', channel)], limit=1)
                if not ch_rec:
                    ch_rec = Channel.create({'name': channel})
                channel_ids.append(ch_rec.id)

            # Marketplace
            ml_marketplace = Marketplace.search([('name', '=', 'Mercado Libre')], limit=1)


            # Procesar imágenes
            picture_ids = []
            for pic in data.get('pictures', []):
                pic_rec = Picture.search([('url', '=', pic['url'])], limit=1)
                if not pic_rec:
                    pic_rec = Picture.create({
                        'url': pic['url'],
                        'secure_url': pic.get('secure_url'),
                        'product_tmpl_id': record.id
                    })
                picture_ids.append(pic_rec.id)

            # Procesar atributos
            attribute_ids = []
            for attr in data.get('attributes', []):
                attr_id_ml = attr.get('id')
                attr_name = attr.get('name')
                val_id_ml = attr.get('value_id')
                val_name = attr.get('value_name')

                # Referencia del atributo en catálogo (vex.meli.attribute)
                ref = self.env['vex.meli.attribute'].search([('meli_attribute_id', '=', attr_id_ml)], limit=1)

                # Valor del atributo (vex.meli.attribute.value)
                val = False
                if ref and val_id_ml:
                    val = self.env['vex.meli.attribute.value'].search([
                        ('attribute_id', '=', ref.id),
                        ('meli_value_id', '=', val_id_ml),
                    ], limit=1)

                # Buscar línea existente del producto
                domain = [
                    ('product_tmpl_id', '=', record.id),
                    ('meli_attribute_ref_id', '=', ref.id if ref else False),
                ]
                if val:
                    domain.append(('meli_values_id', '=', val.id))
                elif val_id_ml:
                    # usar el Char auxiliar cuando no exista el valor en catálogo
                    domain.append(('meli_value_id', '=', val_id_ml))

                attr_rec = Attribute.search(domain, limit=1)
                if not attr_rec:
                    vals = {
                        'product_tmpl_id': record.id,
                        'meli_attribute_ref_id': ref.id if ref else False,
                        'meli_attribute_name': attr_name,
                        'meli_values_id': val.id if val else False,
                        'meli_value_id': val_id_ml or False,  # guarda el ID crudo si no hay registro de valor
                    }
                    attr_rec = Attribute.create(vals)

                attribute_ids.append(attr_rec.id)

            # Procesar variantes
            variant_ids = []
            variations_url = f"https://api.mercadolibre.com/items/{record.meli_product_id}/variations"
            response_var = requests.get(variations_url, headers=headers)
            if response_var.status_code == 200:
                variations = response_var.json()
                for var in variations:
                    var_rec = Variant.search([
                        ('meli_variation_id', '=', var['id']),
                        ('product_tmpl_id', '=', record.id)
                    ], limit=1)
                    if not var_rec:
                        var_rec = Variant.create({
                            'product_tmpl_id': record.id,
                            'meli_variation_id': var['id'],
                            'meli_price': var.get('price'),
                            'meli_available_quantity': var.get('available_quantity'),
                            'meli_attribute_combination': str(var.get('attribute_combinations')),
                        })
                    variant_ids.append(var_rec.id)

            # Escribir campos básicos
            record.write({
                'name': data.get('title'),
                'meli_title': data.get('title'),
                'meli_site_id': data.get('site_id'),
                'meli_seller_id': data.get('seller_id'),
                'meli_user_product_id': data.get('user_product_id'),
                'meli_official_store_id': data.get('official_store_id'),
                'meli_price': data.get('price'),
                'meli_base_price': data.get('base_price'),
                'meli_original_price': data.get('original_price'),
                'meli_currency_id': data.get('currency_id'),
                'meli_initial_quantity': data.get('initial_quantity'),
                'meli_available_quantity': data.get('available_quantity'),
                'meli_sold_quantity': data.get('sold_quantity'),
                'meli_buying_mode': data.get('buying_mode'),
                'meli_listing_type': data.get('listing_type_id'),
                'meli_condition': data.get('condition'),
                'meli_permalink': data.get('permalink'),
                'meli_thumbnail': data.get('thumbnail'),
                'meli_inventory_id': data.get('inventory_id'),
                'meli_category_vex': data.get('category_id'),
                'meli_catalog_product_id': data.get('catalog_product_id'),
                'meli_domain_id': data.get('domain_id'),
                'meli_status': data.get('status'),
                'meli_health': data.get('health'),
                'meli_accepts_mp': data.get('accepts_mercadopago'),
                'meli_shipping_mode': data.get('shipping', {}).get('mode'),
                'meli_free_shipping': data.get('shipping', {}).get('free_shipping'),
                'meli_logistic_type': data.get('shipping', {}).get('logistic_type'),
                'meli_store_pick_up': data.get('shipping', {}).get('store_pick_up'),
                'meli_local_pick_up': data.get('shipping', {}).get('local_pick_up'),
                'meli_shipping_tags': ','.join(data.get('shipping', {}).get('tags', [])),
                'meli_start_time': self.safe_parse_date(data.get('start_time')),
                'meli_stop_time': self.safe_parse_date(data.get('stop_time')),
                'meli_end_time': self.safe_parse_date(data.get('end_time')),
                'meli_expiration_time': self.safe_parse_date(data.get('expiration_time')),
                'meli_last_updated': self.safe_parse_date(data.get('last_updated')),
                'meli_address_line': data.get('seller_address', {}).get('address_line'),
                'meli_zip_code': data.get('seller_address', {}).get('zip_code'),
                'meli_seller_city': data.get('seller_address', {}).get('city', {}).get('name'),
                'meli_seller_state': data.get('seller_address', {}).get('state', {}).get('name'),
                'meli_seller_country': data.get('seller_address', {}).get('country', {}).get('name'),
                'meli_geolocation_lat': data.get('geolocation', {}).get('latitude'),
                'meli_geolocation_lng': data.get('geolocation', {}).get('longitude'),

            })

            # Actualizar relaciones Many2many y One2many
            if hasattr(record, 'meli_tag_ids'):
                record.meli_tag_ids = [(6, 0, tag_ids)]
            if hasattr(record, 'meli_channel_ids'):
                record.meli_channel_ids = [(6, 0, channel_ids)]
            if hasattr(record, 'marketplace_ids'):
                record.marketplace_ids = [(4, ml_marketplace.id)]
            if hasattr(record, 'meli_pictures_ids'):
                record.meli_pictures_ids = [(6, 0, picture_ids)]
            if hasattr(record, 'meli_attribute_ids'):
                record.meli_attribute_ids = [(6, 0, attribute_ids)]
            if hasattr(record, 'meli_variation_ids'):
                record.meli_variation_ids = [(6, 0, variant_ids)]
            
            if record.meli_logistic_type != 'fulfillment':
                location = self.env.ref('odoo-mercadolibre.stock_location_ml_not_full')
            else:
                location = self.env.ref('odoo-mercadolibre.stock_location_ml_full')  

            # Actualizar stock
            record._create_or_update_stock(
                product_id=record.id,
                stock_qty=record.meli_available_quantity,
                stock_location_id=location.id,
                debug=True
            )
        return True
    def action_change_status(self):
        self.ensure_one()

        if not self.ml_publication_code:
            raise UserError("El producto no tiene una publicación asociada en MercadoLibre.")

        # Determinar estado opuesto
        current_status = self.meli_status
        next_status = 'paused' if current_status == 'active' else 'active'

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'change.meli.status.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.id,
                'default_current_status': current_status,
                'default_next_status': next_status,
            }
        }

    def action_update_post(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'update.meli.publication.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.id,
            }
        }

    def set_image_from_meli(self):
        for product in self:
            if not product.meli_pictures_ids:
                _logger.warning(f"Producto {product.name} no tiene imágenes en meli_pictures_ids")
                continue

            first_picture = product.meli_pictures_ids[0]
            if not first_picture.url:
                _logger.warning(f"Imagen sin URL para el producto {product.name}")
                continue

            try:
                response = requests.get(first_picture.url)
                if response.status_code == 200:
                    product.image_1920 = base64.b64encode(response.content)
                    _logger.info(f"Imagen actualizada para el producto {product.name}")
                else:
                    _logger.error(f"No se pudo descargar la imagen: {response.status_code} - {first_picture.url}")
            except Exception as e:
                _logger.error(f"Error descargando imagen para {product.name}: {str(e)}")    
        return True

    def get_stock_forecast_data(self):
        _logger.info("Llamada a get_stock_forecast_data para: %s", self)
        if not self or not self.exists():
            _logger.warning("Recordset inválido. No se puede procesar forecast de stock.")
            return {'labels': [], 'datasets': []}
        
        self.ensure_one()

        # Buscar movimientos de inventario relevantes (realizados)
        moves = self.env['stock.move'].search([
            ('product_id.product_tmpl_id', '=', self.id),
            ('state', '=', 'done'),
            ('date', '!=', False),
        ])

        if not moves:
            _logger.warning("No se encontraron movimientos de stock para el producto %s", self.name)
            return {'labels': [], 'datasets': []}

        # Agrupar por día la suma de cambios netos de inventario
        stock_data = {}
        for move in moves:
            date = move.date.date()
            qty = move.product_uom_qty if move.location_id.usage == 'supplier' or move.location_dest_id.usage == 'internal' else -move.product_uom_qty
            stock_data[date] = stock_data.get(date, 0) + qty

        _logger.info("Datos netos de stock por día: %s", stock_data)

        # Convertir a dataframe
        df = pd.DataFrame(list(stock_data.items()), columns=["ds", "qty"])
        df = df.groupby('ds').sum().reset_index()  # Asegurar un valor por fecha
        df = df.sort_values("ds")

        # Calcular stock acumulado
        df["y"] = df["qty"].cumsum()
        df = df[["ds", "y"]]

        if df["ds"].nunique() < 2:
            _logger.warning("No hay suficientes fechas distintas para entrenar modelo de stock.")
            return {'labels': [], 'datasets': []}

        # Entrenar modelo
        model = Prophet()
        model.fit(df)

        # Predecir 30 días hacia adelante
        future = model.make_future_dataframe(periods=30)
        forecast = model.predict(future)

        labels = forecast['ds'].dt.strftime('%Y-%m-%d').tolist()
        stock_real = forecast['yhat'][:-30].tolist()
        stock_pred = forecast['yhat'][-30:].tolist()

        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Stock Histórico',
                    'data': stock_real + [None] * 30,
                    'borderColor': 'rgb(75, 192, 192)',
                },
                {
                    'label': 'Stock Predicho',
                    'data': [None] * len(stock_real) + stock_pred,
                    'borderColor': 'rgb(255, 206, 86)',
                    'borderDash': [5, 5],
                }
            ]
        }
    
    def get_sales_forecast_data(self):
        _logger.info("Llamada a get_sales_forecast_data para: %s", self)
        if not self or not self.exists():
            _logger.warning("Recordset inválido. No se puede procesar forecast.")
            return {'labels': [], 'datasets': []}
        
        self.ensure_one()
        #_logger.info(f"Obteniendo forecast para product.template ID: {self.id} - {self.name}")
        orders = self.env['sale.order.line'].search([
            ('product_id.product_tmpl_id', '=', self.id),
            ('order_id.state', 'in', ['sale', 'done']),
        ])
        _logger.info("Cantidad de líneas de venta encontradas: %s", len(orders))
        if not orders:
            _logger.warning("No se encontraron órdenes para el producto %s", self.name)
            return {'labels': [], 'datasets': []}

        # Agrupar ventas por fecha
        data = {}
        for line in orders:
            date = line.order_id.date_order.date()
            data[date] = data.get(date, 0) + line.product_uom_qty
        _logger.info("Datos agrupados por fecha: %s", data)
        # Convertir a DataFrame
        df = pd.DataFrame(list(data.items()), columns=["ds", "y"])
        df["ds"] = pd.to_datetime(df["ds"])
        df = df.sort_values("ds")

        # Validación mínima
        if df["ds"].nunique() < 2:
            _logger.warning("No hay suficientes fechas distintas para entrenar modelo.")
            return {'labels': [], 'datasets': []}

        # Entrenar modelo
        model = Prophet()
        model.fit(df)

        # Predecir 5 días adelante
        future = model.make_future_dataframe(periods=30)
        forecast = model.predict(future)

        # Resultado
        labels = forecast['ds'].dt.strftime('%Y-%m-%d').tolist()
        sales = forecast['yhat'][:-30].tolist()
        prediction = forecast['yhat'][-30:].tolist()
        prediction_labels = forecast['ds'].dt.strftime('%Y-%m-%d')[-30:].tolist()

        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Sales',
                    'data': sales + [None] * 5,
                    'borderColor': 'rgb(54, 162, 235)',
                },
                {
                    'label': 'Forecast',
                    'data': [None] * (len(sales)) + prediction,
                    'borderColor': 'rgb(255, 99, 132)',
                    'borderDash': [5, 5],
                }
            ]
        }
        
    @api.model
    def get_top_selling_products(self, limit=10):
        DashboardData = self.env['vex.dashboard.data']
        data_for = "top_selling_products"

        # Buscar registro existente
        record = DashboardData.search([('data_for', '=', data_for)], limit=1)
        if not record or record.last_updated < datetime.now() - timedelta(days=1):
            # Calcular la fecha de hace un mes
            date_from = datetime.now() - timedelta(days=30)
            date_from_str = date_from.strftime('%Y-%m-%d')

            # Buscar las líneas de pedido de venta en el último mes
            sale_order_lines = self.env['sale.order.line'].search([
                ('order_id.state', 'in', ['sale', 'done']),  # Solo contar ventas confirmadas
                ('order_id.date_order', '>=', date_from_str)
            ])

            # Crear un diccionario para contar las cantidades vendidas por producto
            product_sales = {}
            for line in sale_order_lines:
                if line.product_id.id in product_sales:
                    product_sales[line.product_id.id] += line.product_uom_qty
                else:
                    product_sales[line.product_id.id] = line.product_uom_qty

            # Ordenar los productos por cantidad vendida y limitar los resultados
            sorted_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)
            top_products = sorted_products[:limit]

            # Preparar los datos para guardar
            result = []
            for product_id, quantity in top_products:
                product = self.env['product.product'].browse(product_id)
                result.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'quantity_sold': quantity,
                    'stock_available': product.qty_available,
                })

            # Crear o actualizar el registro con los datos calculados
            record_data = {
                'month': 'N/A',  # No aplica para esta función
                'year': 0,  # No aplica
                'new_customers': 0,  # No aplica
                'last_updated': fields.Datetime.now(),
                'data_for': data_for,
                'extra_data': result  # Guardar los datos en un único campo JSON
            }
            if record:
                record.write(record_data)
            else:
                DashboardData.create(record_data)

            return result

        # Retornar los datos desde el campo extra_data
        return record.extra_data if 'extra_data' in record else []

    def _get_marketplace_fee(self, headers, price, listing_type_id, category_id, instance_id):
        """
        Calculates the marketplace fee for a product listing on MercadoLibre.

        This method sends a GET request to the MercadoLibre API to retrieve the sale fee amount
        based on the provided price, listing type, and category for a specific instance.

        Args:
            headers (dict): HTTP headers to include in the API request, typically containing authorization.
            price (float): The price of the product to be listed.
            listing_type_id (str): The identifier for the listing type (e.g., 'gold_pro', 'silver').
            category_id (str): The identifier for the product category.
            instance_id (int): The ID of the 'vex.instance' record representing the MercadoLibre instance.

        Returns:
            float: The calculated marketplace fee. Returns 0.0 if the API request fails.

        Logs:
            - The constructed API URL.
            - The response text if the API request fails.
        """
        instance = self.env['vex.instance'].search([('id', '=', instance_id)])
        code_country = instance.meli_country
        url = f"https://api.mercadolibre.com/sites/{code_country}/listing_prices?price={price}&listing_type_id={listing_type_id}&category_id={category_id}"
        _logger.info(url)
        response = requests.get(url, headers=headers)
        market_fee = 0.0
        if response.status_code == 200:
            res_json = json.loads(response.text)
            market_fee = res_json['sale_fee_amount']
        else:
            _logger.info(response.text)
        return market_fee

    @api.model
    def calculate_table_data(self ,products_dict):    
        for product in products_dict:
            product_info = self.get_product_info(product['product_id'])
            
            product['stock_necessary'] = product_info['forecast_data']['stock_necessary']
            product['current_stock'] = product_info['stock_available']
            product['default_code'] = product_info['default_code']

        
        return products_dict

    @api.model
    def get_product_info(self, product_id):
        # Buscar el producto por ID
        product = self.env['product.product'].browse(product_id)
        
        # Verificar si el producto existe
        if not product.exists():
            return {
                'error': 'Product not found'
            }
        
        # Preparar la información genérica del producto
        product_info = {
            'product_id': product.id,
            'product_name': product.name,
            'default_code': product.default_code,
            'list_price': product.list_price,
            'description': product.description,
            'stock_available': product.qty_available,
        }

         # Calcular la fecha de hace 70 días
        date_from = datetime.now() - timedelta(days=70)
        date_from_str = date_from.strftime('%Y-%m-%d')

         # Buscar las líneas de pedido de venta para el producto en los últimos 70 días
        sale_order_lines = self.env['sale.order.line'].search([
            ('order_id.state', 'in', ['sale', 'done']),
            ('order_id.date_order', '>=', date_from_str),
            ('product_id', '=', product.id),
        ])
        
        # Crear un diccionario para contar las ventas diarias en los últimos 70 días
        daily_sales = {}
        for line in sale_order_lines:
            date_str = line.order_id.date_order.strftime('%Y-%m-%d')
            daily_sales[date_str] = daily_sales.get(date_str, 0) + line.product_uom_qty
        
        # Generar una lista de ventas diarias en los últimos 70 días
        sales_last_70_days = []
        for i in range(70):
            date_check = (date_from + timedelta(days=i)).strftime('%Y-%m-%d')
            sales_last_70_days.append(daily_sales.get(date_check, 0))
        
        # Añadir las ventas diarias al resultado final
        product_info['sales_last_70_days'] = sales_last_70_days
        
        product_info['forecast_data'] = self.action_prediccion(sales_last_70_days)
            
        return product_info

    def action_prediccion(self, dataset):
        sales_last_days = dataset
        num_days = len(sales_last_days)

        end_date = pd.to_datetime('today').normalize()
        start_date = end_date - pd.DateOffset(days=num_days - 1)
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')

        # Crear el DataFrame en el formato que Prophet necesita
        data = pd.DataFrame({
            'ds': date_range,
            'y': [sales_last_days[i] if i < len(sales_last_days) else 0 for i in range(num_days)]
        })

        # Instanciar el modelo Prophet
        model = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=False)
        model.fit(data)

        # Crear el DataFrame para los próximos 7 días
        future = model.make_future_dataframe(periods=7)
        forecast = model.predict(future)

        # Extraer las predicciones para los próximos 7 días y asegurarse de que no haya valores negativos
        forecast_values = forecast[['ds', 'yhat']].tail(7)
        forecast_values['yhat'] = np.maximum(forecast_values['yhat'], 0)  # Ajustar a cero si es negativo

        # Preparar los datos para la salida
        formated_dates = self.format_dates(date_range.tolist())
        formated_forecast_dates = self.format_dates(forecast_values['ds'].tolist())
        stock_necessary = int(forecast_values['yhat'].sum())

        result = {
            'dates': formated_dates,
            'sales': [sale for sale in dataset],  # Usar la lista original para ventas
            'forecast_dates': formated_forecast_dates,
            'forecast_sales': forecast_values['yhat'].tolist(),
            'stock_necessary': stock_necessary,
        }

        return result

    @api.model
    def get_market_opportunity_products(self, offset=0, limit=10):
        current_user = self.env.user 
        meli_instance = current_user.meli_instance_id
        meli_instance.get_access_token()
        access = meli_instance.meli_access_token

        linked_product_ids = self.env['mercado.libre.product'].search([('instance_id','=',meli_instance.id),('state_publi', '!=', None)]).mapped('product.id')
        candidates = self.search([
            ('id', 'not in', linked_product_ids),
            ('recommended_price', '!=', 0),
            ('recommended_price', '!=', False),
            ('recommended_price', '!=', self.list_price),
        ], offset=offset, limit=limit)

        resultados = []
        for prod in candidates:
            if round(prod.recommended_price, 2) == round(prod.list_price, 2):
                continue
            competitiveness = (
                "Más competitivo" if prod.recommended_price < prod.list_price else "Menos competitivo"
            )
            resultados.append({
                "product_tmpl_id": prod.id,
                "product_name": prod.name,
                "current_price": round(prod.list_price, 2),
                "recommended_price": round(prod.recommended_price, 2),
                "competitiveness": competitiveness,
            })
        return resultados

    def format_dates(self,date_range):
        # Formatear las fechas para que solo contengan el día
        return [date.strftime('%Y-%m-%d') for date in date_range]

    def _create_or_update_stock(self, product_id, stock_qty, stock_location_id, debug=False):
        """
        Crea o actualiza el stock de un producto en una ubicación específica usando su ID.

        :param product_id: ID del producto (product.template).
        :param stock_qty: Cantidad de stock a establecer.
        :param stock_location_id: ID de la ubicación (stock.location).
        :param debug: Si es True, activa los logs para esta función.
        """
        
        log = _logger.info if debug else lambda *args, **kwargs: None

        log("Iniciando proceso para actualizar/crear stock para el producto ID: %s en la ubicación ID: %s", product_id, stock_location_id)

        StockQuant = self.env['stock.quant']
        StockLocation = self.env['stock.location']
        Product = self.env['product.product']

        # Verificar si el producto existe
        product = Product.search([('product_tmpl_id', '=', product_id)], limit=1)
        if not product.exists():
            _logger.error("No se encontró un producto con el ID: %s", product_id)
            raise ValueError(f"No se encontró un producto con el ID: {product_id}")

        log("Producto encontrado: %s (ID: %s)", product.name, product.id)

        # Verificar si la ubicación existe
        location = StockLocation.browse(stock_location_id)
        if not location.exists():
            _logger.error("No se encontró la ubicación con ID: %s", stock_location_id)
            raise ValueError(f"No se encontró la ubicación con ID: {stock_location_id}")

        log("Ubicación seleccionada: %s (ID: %s)", location.complete_name, location.id)

        # Buscar el stock.quant para el producto y la ubicación
        quant = StockQuant.search([
            ('product_id', '=', product.id),
            ('location_id', '=', location.id)
        ], limit=1)

        if quant:
            log("Se encontró un stock.quant existente. Actualizando cantidad de %s a %s", quant.quantity, stock_qty)
            quant.quantity = stock_qty
        else:
            log("No se encontró un stock.quant para el producto %s en la ubicación %s. Creando uno nuevo.", product.name, location.complete_name)
            StockQuant.create({
                'product_id': product.id,
                'location_id': location.id,
                'quantity': stock_qty,
                'inventory_quantity': stock_qty,
            })
            log("Nuevo stock.quant creado para el producto %s con cantidad %s en la ubicación %s.", product.name, stock_qty, location.complete_name)

        log("Proceso de actualización/creación de stock completado con éxito.")

    @api.model
    def cron_update_recommended_prices(self):
        """Llenar campo recommended_price consumiendo la API de MercadoLibre."""
        for instance in self.env['vex.instance'].search([('store_type','=','mercadolibre')]):
            _logger.info(f"START CRON cron_update_recommended_prices for instance: {instance.name}")

            instance.get_access_token()
            access_token = instance.meli_access_token
            products = self.search([
                ('store_type','=','mercadolibre'),
                ('instance_id', '=', instance.id),
                ('ml_publication_code', '!=', False),
            ])
            _logger.info(f"Productos encontrados: {len(products)}")
            for product in products:
                try:
                    url = f'https://api.mercadolibre.com/suggestions/items/{product.ml_publication_code}/details'
                    _logger.info(f"URL: {url}")
                    headers = {
                        "Authorization": f"Bearer {access_token}"
                    }
                    response = requests.get(url, headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        suggested_price = data.get("suggested_price").get("amount")
                        
                        if suggested_price:
                            product.recommended_price = suggested_price
                            _logger.info(f"Update recommended_price {product.ml_publication_code}: {suggested_price}")
                    else:
                        _logger.warning(f"API error for {product.ml_publication_code}: {response.status_code}: {response.text}")
                except Exception as e:
                    _logger.error(f"Error fetching price for {product.ml_publication_code}: {str(e)}")
            _logger.info(f"END CRON cron_update_recommended_prices for instance: {instance.name}")

    def get_or_create_meli_category(self, meli_category_id, instance_id):
        Category = self.env['product.category']
        # Llama la API de ML
        url = f"https://api.mercadolibre.com/categories/{meli_category_id}"
        response = requests.get(url)
        if response.status_code != 200:
            raise UserError(f"No se pudo obtener la categoría ML {meli_category_id}: {response.text}")
        data = response.json()
        path = data.get('path_from_root', [])
        parent_id = False
        last_category = None
        for cat in path:
            # Busca si ya existe la categoría en Odoo
            category = Category.search([
                ('meli_category_id', '=', cat['id']),
                ('instance_id', '=', instance_id)
            ], limit=1)
            if not category:
                vals = {
                    'name': cat['name'],
                    'meli_category_id': cat['id'],
                    'parent_id': parent_id,
                    'instance_id': instance_id,
                }
                category = Category.create(vals)
            parent_id = category.id
            last_category = category
        return last_category

    def _set_required_attrs_from_category(self):
        """Crear líneas en meli_attribute_ids con los atributos requeridos de la categoría del producto."""
        for rec in self:
            # limpiar líneas actuales
            rec.meli_attribute_ids = [(5, 0, 0)]
            if not rec.meli_category_id:
                continue

            # Tomar los atributos requeridos de la categoría
            required_attrs = rec.meli_category_id.meli_attribute_ids.filtered(lambda a: a.meli_attribute_required)
            cmds = []
            for a in required_attrs:
                # Si el atributo tiene exactamente un valor posible, lo preseleccionamos
                preselected_value = False
                if hasattr(a, 'value_ids'):
                    values = a.value_ids
                    if len(values) == 1:
                        preselected_value = values.id

                vals = {
                    'meli_attribute_ref_id': a.id,
                    'meli_attribute_name': a.meli_attribute_name,
                }
                if preselected_value:
                    vals['meli_values_id'] = preselected_value
                cmds.append((0, 0, vals))

            if cmds:
                rec.meli_attribute_ids = cmds

    def action_get_category_meli_form_name(self):
        for rec in self:
            if not rec.name:
                raise UserError("El producto debe tener un nombre para buscar su categoria")

            url = f"https://api.mercadolibre.com/sites/MLC/domain_discovery/search?limit=1&q={rec.name}"
            response = requests.get(url)
            if response.status_code != 200:
                raise UserError("Error al consultar la API de MercadoLibre.")

            data = response.json()
            if not data:
                raise UserError("No se encontró ninguna categoría sugerida para este producto.")
            category_id = data[0].get('category_id')
            instance = rec.instance_id

            # Crea toda la jerarquía de categorías
            category = self.get_or_create_meli_category(category_id, instance.id)

            # 1) Actualiza/crea atributos de la categoría en Odoo
            category.action_view_attributes()

            # 2) Asigna la categoría al producto y crea sus líneas de atributos requeridos
            rec.meli_category_id = category.id
            rec.meli_category_vex = category.meli_category_id
            rec._set_required_attrs_from_category()

        return True

    def _update_stock_mercadolibre(self):
        self.ensure_one()
        instance = self.instance_id
        instance.get_access_token()
        ACCESS_TOKEN = instance.meli_access_token
        ITEM_ID = self.meli_product_id

        # Usar la bodega guardada en el producto
        location = self.meli_stock_location_id
        quants = self.env['stock.quant'].search([
            ('product_id', 'in', self.product_variant_ids.ids),
            ('location_id', '=', location.id)
        ])
        available_quantity = max(int(sum(quants.mapped('quantity'))), 0)
        _logger.info("Cantidad enviada a Mercado Libre para %s (ITEM_ID: %s): %s", self.name, ITEM_ID, available_quantity)

        if not ITEM_ID:
            _logger.warning("Producto %s sin ITEM_ID de Mercado Libre configurado.", self.name)
            return False

        url = f"https://api.mercadolibre.com/items/{ITEM_ID}"
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        data = {
            "available_quantity": available_quantity
        }

        _logger.info("Request PUT a Mercado Libre: URL=%s, Headers=%s, Data=%s", url, headers, data)

        response = requests.put(url, headers=headers, json=data)

        if response.status_code == 200:
            _logger.info("✅ Stock actualizado correctamente en Mercado Libre para %s", self.name)
            return True
        else:
            _logger.error("❌ Error al actualizar stock en Mercado Libre de %s: %s", self.name, response.text)
            return False

class ProductTemplateMeliImage(models.Model):
    _name = 'product.template.meli.image'
    _description = 'MercadoLibre Product Images'

    product_tmpl_id = fields.Many2one('product.template', ondelete="cascade")
    url = fields.Char(string="Image URL", help="Original image URL from MercadoLibre", )
    secure_url = fields.Char(string="Secure Image URL", help="HTTPS secure image URL from MercadoLibre")

class ProductTemplateMeliVariation(models.Model):
    _name = 'product.template.meli.variation'
    _description = 'MercadoLibre Product Variations'

    product_tmpl_id = fields.Many2one('product.template', ondelete="cascade")
    meli_variation_id = fields.Char(string="Variation ID", help="Unique variation ID from MercadoLibre")
    meli_price = fields.Float(string="Price", help="Variation price")
    meli_available_quantity = fields.Integer(string="Available Quantity", help="Quantity available for this variation")
    meli_sold_quantity = fields.Integer(string="Sold Quantity", help="Quantity sold for this variation")
    meli_attribute_combination = fields.Text(string="Attribute Combination (JSON)", help="JSON with attribute combinations for the variation")

class ProductTemplateMeliAttribute(models.Model):
    _name = 'product.template.meli.attribute'
    _description = 'MercadoLibre Product Attributes'

    product_tmpl_id = fields.Many2one('product.template', ondelete="cascade")
    meli_attribute_ref_id = fields.Many2one('vex.meli.attribute', string="Atributo ML")
    meli_attribute_name = fields.Char(string="Attribute Name", help="Name of the attribute")

    # Cambiar de Char -> Many2one
    meli_value_id = fields.Char(string="Value ID", help="Identifier of the attribute value")
    meli_values_id = fields.Many2one(
        'vex.meli.attribute.value', 
        string="Valor ML"
    )
    meli_value_name = fields.Char(
        related='meli_values_id.meli_value_name', 
        string="Value Name", 
        store=True
    )

    meli_category_vex = fields.Char(
        related="product_tmpl_id.meli_category_vex", 
        store=False
    )

    meli_category_id = fields.Many2one(
        related="product_tmpl_id.meli_category_id",
        string="ML Category",
        store=False
    )

    @api.onchange('meli_attribute_ref_id')
    def _onchange_meli_attribute_ref_id(self):
        if self.meli_attribute_ref_id:
            self.meli_attribute_name = self.meli_attribute_ref_id.meli_attribute_name
            # Si el atributo no tiene valores, limpiar el campo Many2one y permitir escribir
            values = self.env['vex.meli.attribute.value'].search([('attribute_id', '=', self.meli_attribute_ref_id.id)])
            if not values:
                self.meli_values_id = False
                # Aquí puedes mostrar un mensaje o habilitar el campo meli_value_name
            else:
                self.meli_value_name = False  # Limpiar si hay valores predefinidos

    @api.onchange('meli_attribute_ref_id')
    def _onchange_meli_attribute_ref_id(self):
        if self.meli_attribute_ref_id:
            self.meli_attribute_name = self.meli_attribute_ref_id.meli_attribute_name
            self.meli_values_id = False  # Limpiar valor anterior si cambia el atributo

class ProductMeliTag(models.Model):
    _name = 'product.meli.tag'
    _description = 'MercadoLibre Tag'

    name = fields.Char(string='Tag', required=True, index=True)

class ProductMeliChannel(models.Model):
    _name = 'product.meli.channel'
    _description = 'MercadoLibre Channel'

    name = fields.Char(string='Channel', required=True, index=True)

class ProductMarketplace(models.Model):
    _name = 'product.marketplace'
    _description = 'Marketplace'

    name = fields.Char(string='Marketplace Name', required=True, index=True)

# Modelos del wizard
class VexPublishProductWizardImage(models.TransientModel):
    _name = 'vex.publish.product.wizard.image'
    _description = 'MercadoLibre Product Images Wizard'

    wizard_id = fields.Many2one('vex.publish.product.wizard', ondelete="cascade")
    # Copia los campos que necesitas del modelo original
    url = fields.Char(string="Imagen URL")
    secure_url = fields.Char(string="Secure Image URL")
    # Puedes añadir otros campos que solo sean relevantes para el wizard

class VexPublishProductWizardAttribute(models.TransientModel):
    _name = 'vex.publish.product.wizard.attribute'
    _description = 'Atributo temporal para el wizard de publicación'
    
    wizard_id = fields.Many2one('vex.publish.product.wizard', string='Wizard')
    meli_category_id = fields.Many2one(
        'product.category',
        related="wizard_id.meli_category_id",
        store=False,
        string="Categoría MercadoLibre"
    )
    meli_category_vex = fields.Char(related="wizard_id.meli_category_vex", store=False)
    meli_attribute_ref_id = fields.Many2one('vex.meli.attribute', string="Atributo ML")
    meli_values_id = fields.Many2one('vex.meli.attribute.value', string="Valor ML")
    meli_attribute_name = fields.Char(related='meli_attribute_ref_id.meli_attribute_name', string="Attribute Name", store=True)
    meli_value_name = fields.Char(related='meli_values_id.meli_value_name', string="Value Name", store=True)
