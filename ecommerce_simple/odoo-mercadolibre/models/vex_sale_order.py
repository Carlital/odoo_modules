# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import json
import logging
_logger = logging.getLogger(__name__)
import base64
from PyPDF2 import PdfMerger
import io
import pytz
from pytz import timezone, UTC
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import unicodedata

from prophet import Prophet
import pandas as pd
import numpy as np

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    meli_order_id = fields.Char(string="Meli Order ID", help="Unique identifier of the order in MercadoLibre.")
    meli_date_created = fields.Datetime(string="Meli Date Created", help="Date and time the order was created in MercadoLibre.")
    meli_last_updated = fields.Datetime(string="Meli Last Updated", help="Date and time of the last update to the order in MercadoLibre.")
    meli_date_closed = fields.Datetime(string="Meli Date Closed", help="Date and time the order was closed in MercadoLibre.")
    meli_pack_id = fields.Char(string="Meli Pack ID", help="ID of the pack that groups multiple orders into one shipment.")
    meli_fulfilled = fields.Boolean(string="Meli Fulfilled", help="Indicates whether the order was fulfilled by the seller.")
    meli_buying_mode = fields.Char(string="Meli Buying Mode", help="Buying mode such as 'buy_it_now'.")
    meli_shipping_cost = fields.Float(string="Meli Shipping Cost", help="Shipping cost of the order.")
    meli_total_amount = fields.Float(string="Meli Total Amount", help="Total amount of the order.")
    meli_paid_amount = fields.Float(string="Meli Paid Amount", help="Amount paid by the buyer.")
    meli_currency_id_api = fields.Char(string="Meli Currency ID", help="Currency code used in the order (e.g. 'PEN', 'USD').")
    meli_status = fields.Char(string="Meli Status", help="Current status of the order (e.g. 'paid', 'cancelled').")
    meli_status_detail = fields.Char(string="Meli Status Detail", help="Detailed description of the current order status.")
    meli_tags = fields.Char(string="Meli Tags", help="Comma-separated tags assigned to the order by MercadoLibre.")
    meli_internal_tags = fields.Char(string="Meli Internal Tags", help="Internal tags for order classification by MercadoLibre.")
    meli_manufacturing_ending_date = fields.Datetime(string="Meli Manufacturing Ending Date", help="Manufacturing end date if the item is made-to-order.")
    meli_shipping_id = fields.Char(string="Meli Shipping ID", help="Shipping ID linked to the order.")

    # Buyer info
    meli_buyer_id = fields.Char(string="Meli Buyer ID", help="ID of the buyer in MercadoLibre.")
    meli_buyer_nickname = fields.Char(string="Meli Buyer Nickname", help="Nickname of the buyer.")
    meli_buyer_first_name = fields.Char(string="Meli Buyer First Name", help="First name of the buyer.")
    meli_buyer_last_name = fields.Char(string="Meli Buyer Last Name", help="Last name of the buyer.")

    # Seller info
    meli_seller_id = fields.Char(string="Meli Seller ID", help="ID of the seller in MercadoLibre.")

    # Feedback
    meli_feedback_seller_id = fields.Char(string="Meli Feedback Seller ID", help="ID of the feedback given to the seller.")
    meli_feedback_buyer_id = fields.Char(string="Meli Feedback Buyer ID", help="ID of the feedback given to the buyer.")

    # Context
    meli_context_channel = fields.Char(string="Meli Context Channel", help="Channel from which the order originated (e.g. 'marketplace').")
    meli_context_site = fields.Char(string="Meli Context Site", help="MercadoLibre site where the order was made (e.g. 'MLM', 'MLA').")
    meli_context_flows = fields.Char(string="Meli Context Flows", help="Comma-separated list of flows associated with the order.")

    # Cancel Detail
    meli_cancel_group = fields.Char(string="Meli Cancel Group", help="Group responsible for the cancellation (e.g. 'buyer', 'seller').")
    meli_cancel_code = fields.Char(string="Meli Cancel Code", help="Cancellation reason code.")
    meli_cancel_description = fields.Text(string="Meli Cancel Description", help="Detailed description of the cancellation reason.")
    meli_cancel_requested_by = fields.Char(string="Meli Cancel Requested By", help="User or system that requested the cancellation.")
    meli_cancel_date = fields.Datetime(string="Meli Cancel Date", help="Date and time of the cancellation.")
    meli_cancel_application_id = fields.Char(string="Meli Cancel Application ID", help="ID of the application that requested the cancellation.")

    # Order Request
    meli_order_request_change = fields.Char(string="Meli Order Request Change", help="Indicates whether the buyer requested a change.")
    meli_order_request_return = fields.Char(string="Meli Order Request Return", help="Indicates whether the buyer requested a return.")

    # One2many
    meli_mediation_ids = fields.One2many('meli.order.mediation', 'order_id', string="Meli Mediations", help="List of mediation claims linked to this order.")
    meli_item_ids = fields.One2many('meli.order.item', 'order_id', string="Meli Order Items", help="List of items included in the order.")
    meli_payment_ids = fields.One2many('meli.order.payment', 'order_id', string="Meli Payments", help="List of payments made for the order.")
    meli_tag_ids = fields.Many2many('sale.meli.tag', string="Meli Tags", help="Many2many relation to tag records linked to this order.")
    meli_internal_tag_ids = fields.Many2many('sale.meli.internal.tag', string="Meli Internal Tags", help="Many2many relation to internal tags from MercadoLibre.")
    meli_context_flow_ids = fields.Many2many('sale.meli.context.flow', string="Meli Context Flows", help="Many2many relation to context flows associated with this order.")
    meli_json_data = fields.Text("JSON ORDER MercadoLibre", help="Raw JSON response of the order received from MercadoLibre.")

    #SHIPPING FIELDS

    meli_shipping_tracking_number = fields.Char("Tracking Number", help="Tracking number assigned to the shipment.")
    meli_shipping_status = fields.Char("Shipping Status", help="Current shipping status from MercadoLibre.")
    meli_shipping_logistic_type = fields.Char("Logistic Type", help="Logistic type used for delivery (e.g., fulfillment, drop_off).")
    meli_shipping_mode = fields.Char("Shipping Mode", help="Shipping mode used (e.g., me2).")
    meli_shipping_order_cost = fields.Float("Order Cost", help="Total cost of the shipping service.")
    meli_shipping_base_cost = fields.Float("Base Cost", help="Base cost of the shipping service before discounts.")
    meli_shipping_tracking_method = fields.Char("Tracking Method", help="The method used for tracking, like MEL Distribution.")
    meli_shipping_sender_id = fields.Char("Sender ID", help="ID of the sender in MercadoLibre.")
    meli_shipping_receiver_id = fields.Char("Receiver ID", help="ID of the receiver in MercadoLibre.")
    meli_shipping_service_id = fields.Char("Shipping Service ID", help="ID of the logistics/shipping service.")
    meli_shipping_priority_class_id = fields.Char("Priority Class ID", help="Priority level of the shipping service.")
    meli_shipping_last_updated = fields.Datetime("Last Updated", help="Date and time when shipping info was last updated.")
    meli_shipping_date_created = fields.Datetime("Shipping Created Date", help="Date and time when the shipping was created.")
    meli_shipping_date_first_printed = fields.Datetime("Date First Printed", help="Date when the shipping label was first printed.")
    meli_shipping_created_by = fields.Char("Shipping Created By", help="Who created the shipping (e.g., receiver).")
    meli_shipping_marketplace = fields.Char("Marketplace", help="Marketplace origin of the shipping.")
    meli_shipping_site_id = fields.Char("Site ID", help="Site where the order was made (e.g., MLA, MLM).")

    # One2many y Many2many
    meli_shipping_substatus_history_ids = fields.One2many('sale.meli.shipping.substatus', 'order_id', string="Substatus History")
    meli_shipping_item_ids = fields.One2many('sale.meli.shipping.item', 'order_id', string="Shipping Items")
    meli_shipping_tag_ids = fields.Many2many('sale.meli.shipping.tag', string="Shipping Tags")
    meli_shipping_item_type_ids = fields.Many2many('sale.meli.shipping.item.type', string="Item Types")
    # Shipping Option
    meli_shipping_option_id = fields.Char("Shipping Option ID", help="ID of the shipping option used.")
    meli_shipping_option_name = fields.Char("Shipping Option Name", help="Name of the shipping option.")
    meli_shipping_option_cost = fields.Float("Shipping Option Cost", help="Cost of the shipping option.")
    meli_shipping_option_speed = fields.Char("Shipping Option Speed", help="Shipping speed description.")

    # Receiver Address
    meli_receiver_city = fields.Char("Receiver City", help="City of the receiver.")
    meli_receiver_state = fields.Char("Receiver State", help="State of the receiver.")
    meli_receiver_country = fields.Char("Receiver Country", help="Country of the receiver.")
    meli_receiver_zip_code = fields.Char("Receiver Zip Code", help="ZIP/Postal code of the receiver.")
    meli_receiver_street_name = fields.Char("Receiver Street", help="Street name of the receiver's address.")
    meli_receiver_street_number = fields.Char("Receiver Street Number", help="Street number.")
    meli_receiver_latitude = fields.Char("Receiver Latitude", help="Latitude coordinate.")
    meli_receiver_longitude = fields.Char("Receiver Longitude", help="Longitude coordinate.")

    # Sender Address
    meli_sender_city = fields.Char("Sender City", help="City of the sender.")
    meli_sender_state = fields.Char("Sender State", help="State of the sender.")
    meli_sender_country = fields.Char("Sender Country", help="Country of the sender.")
    meli_sender_zip_code = fields.Char("Sender Zip Code", help="ZIP/Postal code of the sender.")
    meli_sender_street_name = fields.Char("Sender Street", help="Street name of the sender's address.")
    meli_sender_street_number = fields.Char("Sender Street Number", help="Street number.")
    meli_sender_latitude = fields.Char("Sender Latitude", help="Latitude coordinate.")
    meli_sender_longitude = fields.Char("Sender Longitude", help="Longitude coordinate.")
    meli_shipping_option_list_cost = fields.Float("Shipping Option List Cost", help="Original list cost of the shipping option before discounts.")


    # JSON
    meli_shipping_json_data = fields.Text("Raw JSON Shipping", help="Raw JSON data from the shipping API.")
    meli_item_cost = fields.Float("Item Cost", help="Total cost of the items in the order.", compute='_get_item_cost')
    meli_net_gain = fields.Float("Net Gain", help="Net gain from the order after costs and fees.", compute='_compute_net_gain')
    meli_sale_fee = fields.Float("Sale Fee", help="Sale fee for the order.", compute='_compute_sale_fee')
    meli_date_create_without_time = fields.Date(string="Meli Date Created (without time)", help="Date created without time component, used for filtering.")

    def action_copy_datetime_to_date(self):
        user_tz = timezone(self.env.user.tz or 'UTC')

        for record in self:
            if record.meli_date_created:
                # Convertir a tz local antes de sacar la fecha real percibida por el usuario
                meli_dt_utc = record.meli_date_created.replace(tzinfo=UTC)
                meli_dt_local = meli_dt_utc.astimezone(user_tz)
                record.meli_date_create_without_time = meli_dt_local.date()
            else:
                record.meli_date_create_without_time = False

    def _compute_sale_fee(self):
        for record in self:
            if record.meli_item_ids:
                # Sumar las tarifas de venta de todos los items
                record.meli_sale_fee = sum(item.meli_sale_fee for item in record.meli_item_ids)
            else:
                record.meli_sale_fee = 0.0

    def _compute_net_gain(self):
        for record in self:
            if record.meli_total_amount and record.meli_paid_amount and record.meli_item_cost:
                # Calcular ganancia neta: Total pagado - Costo de los items
                record.meli_net_gain = record.meli_paid_amount - record.meli_item_cost - record.meli_shipping_cost - record.meli_sale_fee
            else:
                record.meli_net_gain = 0.0


    def _get_item_cost(self):
        for record in self:
            if record.order_line:
                for item in record.order_line:
                    record.meli_item_cost = item.product_id.standard_price
            else:
                record.meli_item_cost = 0.0

    def parse_meli_datetime(self, value):
        if value:
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone().replace(tzinfo=None)
            except Exception:
                return False
        return False
    
    def get_tag_ids(self, model, tag_list):
        Tag = self.env[model]
        ids = []
        for name in tag_list:
            tag = Tag.search([('name', '=', name)], limit=1)
            if not tag:
                tag = Tag.create({'name': name})
            ids.append(tag.id)
        return [(6, 0, ids)]

    def safe_get(self, data, *keys):
        for key in keys:
            if not isinstance(data, dict):
                return None
            data = data.get(key)
            if data is None:
                return None
        return data

    def action_get_details(self):
        """Main entry: Sync MercadoLibre order or pack into Sale Order."""
        _logger.info("=== [ML SYNC] Inicio de action_get_details para sale.order ID=%s, meli_order_id=%s ===",
                    self.id, self.meli_order_id)

        # Validaciones iniciales
        if not self.meli_order_id:
            _logger.error("[ML SYNC] Error: No se definió meli_order_id en la orden ID=%s", self.id)
            raise UserError("Debe establecer primero el campo Meli Order ID.")
        if not self.instance_id or not self.instance_id.meli_access_token:
            _logger.error("[ML SYNC] Error: No se definió instance_id o access_token en la orden ID=%s", self.id)
            raise UserError("No se ha definido el token de acceso en la instancia vinculada.")

        access_token = self.instance_id.meli_access_token
        headers = {'Authorization': f'Bearer {access_token}'}

        # 1. Intentar como Orden
        order_url = f"https://api.mercadolibre.com/orders/{self.meli_order_id}"
        order_response = requests.get(order_url, headers=headers)

        order_data = {}
        order_items = []
        pack_id = None

        if order_response.status_code == 200:
            # Es una orden simple (o una orden que pertenece a un pack)
            _logger.info("[ML SYNC] Se encontró la orden ML con ID=%s.", self.meli_order_id)
            order_data = order_response.json()
            pack_id = order_data.get("pack_id")
            if pack_id:
                # Si la orden pertenece a un pack, obtenemos todas las órdenes del pack para consolidar
                _logger.info("[ML SYNC] La orden pertenece al pack %s. Consolidando ítems del pack.", pack_id)
                all_pack_orders_data = self._meli_get_pack_orders(pack_id, headers)
                consolidated_items = []
                for sub_order_data in all_pack_orders_data:
                    sub_order_id = sub_order_data.get('id')
                    for item in sub_order_data.get("order_items", []):
                        item['sub_order_id'] = sub_order_id
                        consolidated_items.append(item)
                order_items = consolidated_items
                self.is_package = True
            else:
                # Es una orden simple
                order_items = order_data.get("order_items", [])
                # CORRECCIÓN: Asignar sub_order_id a cada item
                for item in order_items:
                    item['sub_order_id'] = self.meli_order_id

        elif order_response.status_code == 404:
            # 2. Si falla, intentar como Pack
            _logger.warning("[ML SYNC] Orden %s no encontrada, intentando como Pack ID.", self.meli_order_id)
            pack_id = self.meli_order_id # El ID principal es el del pack
            all_pack_orders_data = self._meli_get_pack_orders(pack_id, headers)
            if not all_pack_orders_data:
                raise UserError(f"El ID {pack_id} no se encontró ni como orden ni como pack en Mercado Libre.")
            
            order_data = all_pack_orders_data[0]
            # Usamos los datos de la primera orden del pack como base para el partner, etc.
            consolidated_items = []
            for sub_order_data in all_pack_orders_data:
                sub_order_id = sub_order_data.get('id')
                for item in sub_order_data.get("order_items", []):
                    item['sub_order_id'] = sub_order_id 
                    consolidated_items.append(item)
            
            order_items = consolidated_items
            self.is_package = True
        else:
            # Otro error de API
            raise UserError(f"Error al consultar la API de Mercado Libre: {order_response.text}")

        # Guardar JSON para auditoría
        self.meli_json_data = json.dumps(order_data, indent=4, ensure_ascii=False)
        _logger.debug("[ML SYNC] meli_json_data guardado en sale.order ID=%s", self.id)

        # 🧑‍🤝‍🧑 Partner
        _logger.info("[ML SYNC] Buscando o creando partner para la orden ID=%s ...", self.id)
        partner_id = self._get_or_create_partner(order_data, self)
        _logger.info("[ML SYNC] Partner asignado: ID=%s - Nombre=%s", partner_id.id, partner_id.name)

        # 🧹 Limpiar líneas anteriores
        _logger.info("[ML SYNC] Limpiando mediations, items y payments previos para sale.order ID=%s ...", self.id)
        self.meli_mediation_ids.unlink()
        self.meli_item_ids.unlink()
        self.meli_payment_ids.unlink()

        # 📦 Preparar líneas de venta
        _logger.info("[ML SYNC] Preparando líneas de venta para %s ítems ...", len(order_items))
        order_lines, meli_items = self._prepare_order_lines(order_items, self)
        _logger.info("[ML SYNC] Líneas preparadas: %s | Ítems ML: %s", len(order_lines), len(meli_items))

        # Valores comunes de la orden
        vals = {
            # Identificación
            #'partner_id': partner_id.id,
            'meli_pack_id': str(pack_id) if pack_id else False,
            'meli_sale_id': str(pack_id) if pack_id else self.meli_order_id,

            # Fechas
            'date_order': self.parse_meli_datetime(order_data.get("date_created")),
            'meli_date_created': self.parse_meli_datetime(order_data.get("date_created")),
            'meli_last_updated': self.parse_meli_datetime(order_data.get("last_updated")),
            'meli_date_closed': self.parse_meli_datetime(order_data.get("date_closed")),

            # Datos de orden
            'meli_fulfilled': order_data.get("fulfilled"),
            'meli_buying_mode': order_data.get("buying_mode"),
            'meli_total_amount': order_data.get("total_amount") or 0.0,
            'meli_paid_amount': order_data.get("paid_amount") or 0.0,
            'meli_currency_id_api': order_data.get("currency_id"),
            'meli_status': order_data.get("status"),
            'meli_status_detail': order_data.get("status_detail"),

            # Tags
            'meli_tags': ','.join(order_data.get("tags", [])),
            'meli_internal_tags': ','.join(order_data.get("internal_tags", [])),
            'meli_tag_ids': self.get_tag_ids('sale.meli.tag', order_data.get("tags", [])),
            'meli_internal_tag_ids': self.get_tag_ids('sale.meli.internal.tag', order_data.get("internal_tags", [])),
            'meli_context_flow_ids': self.get_tag_ids('sale.meli.context.flow', order_data.get("context", {}).get("flows", [])),

            # Buyer / Seller
            'meli_shipping_id': str(self.safe_get(order_data, "shipping", "id")),
            'meli_buyer_id': str(self.safe_get(order_data, "buyer", "id")),
            'meli_buyer_nickname': self.safe_get(order_data, "buyer", "nickname"),
            'meli_buyer_first_name': self.safe_get(order_data, "buyer", "first_name"),
            'meli_buyer_last_name': self.safe_get(order_data, "buyer", "last_name"),
            'meli_seller_id': str(self.safe_get(order_data, "seller", "id")),
            'meli_feedback_seller_id': str(self.safe_get(order_data, "feedback", "seller", "id")),
            'meli_feedback_buyer_id': str(self.safe_get(order_data, "feedback", "buyer", "id")),

            # Context
            'meli_context_channel': self.safe_get(order_data, "context", "channel"),
            'meli_context_site': self.safe_get(order_data, "context", "site"),
            'meli_context_flows': ','.join(order_data.get("context", {}).get("flows", [])),

            # Cancel
            'meli_cancel_group': self.safe_get(order_data, "cancel_detail", "group"),
            'meli_cancel_code': self.safe_get(order_data, "cancel_detail", "code"),
            'meli_cancel_description': self.safe_get(order_data, "cancel_detail", "description"),
            'meli_cancel_requested_by': self.safe_get(order_data, "cancel_detail", "requested_by"),
            'meli_cancel_date': self.parse_meli_datetime(self.safe_get(order_data, "cancel_detail", "date")),
            'meli_cancel_application_id': self.safe_get(order_data, "cancel_detail", "application_id"),

            # Relaciones
            'meli_mediation_ids': [(0, 0, {'meli_mediation_id': str(m.get("id"))}) for m in order_data.get("mediations", [])],
            'meli_item_ids': meli_items,  # ya lo tenías con _prepare_order_lines
            'meli_payment_ids': [(0, 0, {
                'meli_payment_id': str(p["id"]),
                'meli_payer_id': str(p["payer_id"]),
                'meli_collector_id': self.safe_get(p, "collector", "id"),
                'meli_reason': p.get("reason"),
                'meli_site_id': p.get("site_id"),
                'meli_payment_method_id': p.get("payment_method_id"),
                'meli_currency_id': p.get("currency_id"),
                'meli_installments': p.get("installments"),
                'meli_issuer_id': p.get("issuer_id"),
                'meli_operation_type': p.get("operation_type"),
                'meli_payment_type': p.get("payment_type"),
                'meli_status': p.get("status"),
                'meli_status_detail': p.get("status_detail"),
                'meli_transaction_amount': p.get("transaction_amount"),
                'meli_transaction_amount_refunded': p.get("transaction_amount_refunded"),
                'meli_taxes_amount': p.get("taxes_amount"),
                'meli_shipping_cost': p.get("shipping_cost"),
                'meli_coupon_amount': p.get("coupon_amount"),
                'meli_overpaid_amount': p.get("overpaid_amount"),
                'meli_total_paid_amount': p.get("total_paid_amount"),
                'meli_date_approved': self.parse_meli_datetime(p.get("date_approved")),
                'meli_date_created': self.parse_meli_datetime(p.get("date_created")),
                'meli_date_last_modified': self.parse_meli_datetime(p.get("date_last_modified")),
                'meli_marketplace_fee': p.get("marketplace_fee"),
            }) for p in order_data.get("payments", [])],

            # Order lines y almacén
            #'order_line': [(5, 0, 0)] + order_lines,
            #'warehouse_id': self._get_default_warehouse(order_items),
        }
        if self.state=='draft':
            vals['partner_id'] = partner_id.id
            vals['order_line'] = [(5, 0, 0)] + order_lines
            vals['warehouse_id'] = self._get_default_warehouse(order_items)       
        _logger.debug("[ML SYNC] Valores que se escribirán en sale.order ID=%s: %s", self.id, vals)

        if pack_id:
            existing_order = self.env['sale.order'].search([
                ('meli_sale_id', '=', str(pack_id))
            ], limit=1)
            if existing_order and existing_order.id != self.id:
                _logger.info(f"Ya existe una sale.order para el pack {pack_id}: {existing_order.name}")
                existing_order.write(vals)
                return True
            
        # Crear o actualizar orden
        if self.state == 'draft':
            _logger.info("[ML SYNC] La orden está en estado 'draft'. Escribiendo y confirmando...")
            self.write(vals)
            self.action_confirm()
            _logger.info("[ML SYNC] Orden ID=%s confirmada correctamente.", self.id)
        else:
            _logger.info("[ML SYNC] La orden NO está en estado draft. Solo se actualizan valores.")
            self.write(vals)

        _logger.info("=== [ML SYNC] Fin de action_get_details para sale.order ID=%s ===", self.id)
        return True



    # ============================================================
    # Métodos auxiliares
    # ============================================================

    def _meli_get_order(self, order_id, headers):
        """Get order detail from MercadoLibre API."""
        url = f"https://api.mercadolibre.com/orders/{order_id}"
        response = requests.get(url, headers=headers)
        if response.status_code not in (200, 206):
            raise UserError(f"Error al consultar orden {order_id}: {response.status_code} - {response.text}")
        return response.json()

    def _meli_get_pack_orders(self, pack_id, headers):
        """Get all orders inside a pack."""
        url = f"https://api.mercadolibre.com/packs/{pack_id}"
        response = requests.get(url, headers=headers)
        if response.status_code not in (200, 206):
            raise UserError(f"Error al consultar pack {pack_id}: {response.status_code} - {response.text}")
        data_pack = response.json()
        orders = []
        for order in data_pack.get("orders", []):
            od = self._meli_get_order(order.get("id"), headers)
            orders.append(od)
        return orders

    def _get_or_create_partner(self, order_data, record):
        """Get or create partner based on buyer nickname."""
        ml_marketplace = self.env['vex.marketplace'].search([('name', '=', 'Mercado Libre')], limit=1)
        buyer_nickname = self.safe_get(order_data, "buyer", "nickname")
        if not buyer_nickname:
            raise UserError("No se pudo obtener el nickname del comprador desde la API de MercadoLibre.")

        partner = self.env['res.partner'].search([('nickname', '=', buyer_nickname)], limit=1)
        if not partner:
            partner = self.env['res.partner'].create({
                'name': order_data.get("buyer", {}).get("first_name", buyer_nickname) + " " + order_data.get("buyer", {}).get("last_name", ""),
                'nickname': buyer_nickname,
                'instance_id': record.instance_id.id,
                'marketplace_ids': [(4, ml_marketplace.id)],
                'company_id': record.company_id.id if record.company_id else False
            })
        return partner

    def _prepare_order_lines(self, order_items, record):
        order_lines = []
        meli_items = []
        product_model = self.env['product.template']
        uom_model = self.env['uom.uom']

        for i in order_items:
            product = product_model.search([('meli_product_id', '=', i["item"]["id"])], limit=1)
            if not product:
                product = product_model.create({
                    'name': i["item"]["title"],
                    'meli_product_id': i["item"]["id"],
                    'detailed_type': 'product',
                    'instance_id': record.instance_id.id,
                    'marketplace_ids': [(4, self.env.ref('odoo-mercadolibre.vex_marketplace_mercadolibre').id)],
                    'company_id': record.company_id.id if record.company_id else False
                })
                product.action_get_details()
                product.set_image_from_meli()
                product.action_download_stock()

            uom = product.uom_id or uom_model.search([('name', 'ilike', 'Unit')], limit=1)
            product_product_id = self.env['product.product'].search([('product_tmpl_id', '=', product.id)], limit=1)

            sub_order_id = i.get('sub_order_id') or record.meli_order_id

            order_lines.append((0, 0, {
                'product_id': product_product_id.id if product_product_id else False,
                'name': i["item"]["title"],
                'product_uom_qty': i["quantity"],
                'price_unit': i["unit_price"],
                'product_uom': uom.id if uom else False,
                'display_type': False,
                'order_meli_id': str(sub_order_id) if sub_order_id else False,  
            }))

            meli_items.append((0, 0, {
                'meli_item_id': i["item"]["id"],
                'meli_title': i["item"]["title"],
                'meli_category_id': i["item"]["category_id"],
                'meli_variation_id': i["item"].get("variation_id"),
                'meli_warranty': i["item"].get("warranty"),
                'meli_condition': i["item"].get("condition"),
                'meli_quantity': i["quantity"],
                'meli_unit_price': i["unit_price"],
                'meli_full_unit_price': i["full_unit_price"],
                'meli_currency_id': i["currency_id"],
            }))

        return order_lines, meli_items

    def _get_default_warehouse(self, order_items):
        """Select default warehouse based on logistic type of first item."""
        if not order_items:
            return False
        first_item = order_items[0]
        product = self.env['product.template'].search([('meli_product_id', '=', first_item["item"]["id"])], limit=1)
        if product and product.meli_logistic_type == 'fulfillment':
            #return self.env.ref('odoo-mercadolibre.stock_warehouse_mercadolibre_full').id
            return self.instance_id.ml_full_warehouse_id.id
        #return self.env.ref('odoo-mercadolibre.stock_warehouse_mercadolibre_not_full').id
        return self.instance_id.ml_not_full_warehouse_id.id

    def action_confirm_delivery(self):
        for order in self:
            pickings = self.env['stock.picking'].search([
                ('origin', '=', self.name),
                ('state', 'not in', ['done', 'cancel'])
            ])
            for picking in pickings:
                if picking.state == 'draft':
                    picking.action_confirm()
                if picking.state in ['confirmed', 'assigned']:
                    picking.action_assign()

                # Asegurar que se llenen las cantidades entregadas
                for move_line in picking.move_ids_without_package:
                    if move_line.quantity == 0.0:
                        move_line.quantity = move_line.product_uom_qty

                # Validar (confirma la entrega sin abrir wizard)
                picking.button_validate()

    def action_get_shipping_details(self):
        for order in self:
            if not order.meli_shipping_id or not order.instance_id:
                continue

            token = order.instance_id.meli_access_token
            headers = {
                'Authorization': f'Bearer {token}'
            }

            url = f'https://api.mercadolibre.com/shipments/{order.meli_shipping_id}'
            response = requests.get(url, headers=headers)

            if response.status_code not in (200, 206):
                raise UserError(f"Error al obtener detalles de envío: {response.status_code} - {response.text}")

            data = response.json()

            # Guardar JSON crudo
            order.meli_shipping_json_data = json.dumps(data,indent=4, ensure_ascii=False)

            # Evitar duplicados
            order.meli_shipping_substatus_history_ids.unlink()
            order.meli_shipping_item_ids.unlink()
            order.meli_shipping_tag_ids = [(5, 0, 0)]
            order.meli_shipping_item_type_ids = [(5, 0, 0)]

            # Substatus history
            for entry in data.get('substatus_history', []):
                self.env['sale.meli.shipping.substatus'].create({
                    'order_id': order.id,
                    'date': order.parse_meli_datetime(entry.get('date')),
                    'substatus': entry.get('substatus'),
                    'status': entry.get('status'),
                })

            # Shipping items
            for item in data.get('shipping_items', []):
                self.env['sale.meli.shipping.item'].create({
                    'order_id': order.id,
                    'item_id': item.get('id'),
                    'description': item.get('description'),
                    'quantity': item.get('quantity'),
                    'dimensions': item.get('dimensions'),
                    'sender_id': item.get('sender_id'),
                    'user_product_id': item.get('user_product_id'),
                    'origin': item.get('dimensions_source', {}).get('origin'),
                })

            # Tags
            tag_model = self.env['sale.meli.shipping.tag']
            tag_ids = []
            for tag in data.get('tags', []):
                tag_rec = tag_model.search([('name', '=', tag)], limit=1)
                if not tag_rec:
                    tag_rec = tag_model.create({'name': tag})
                tag_ids.append(tag_rec.id)
            order.meli_shipping_tag_ids = [(6, 0, tag_ids)]

            # Item Types
            type_model = self.env['sale.meli.shipping.item.type']
            type_ids = []
            for item_type in data.get('items_types', []):
                type_rec = type_model.search([('name', '=', item_type)], limit=1)
                if not type_rec:
                    type_rec = type_model.create({'name': item_type})
                type_ids.append(type_rec.id)
            order.meli_shipping_item_type_ids = [(6, 0, type_ids)]
            shipping_option = data.get('shipping_option', {})
            receiver = data.get('receiver_address', {})
            sender = data.get('sender_address', {})
            # Campos directos (evitando nulos)
            order.update({
                'meli_shipping_tracking_number': data.get('tracking_number'),
                'meli_shipping_status': data.get('status'),
                'meli_shipping_logistic_type': data.get('logistic_type'),
                'meli_shipping_mode': data.get('mode'),
                'meli_shipping_order_cost': data.get('order_cost'),
                'meli_shipping_base_cost': data.get('base_cost'),
                'meli_shipping_tracking_method': data.get('tracking_method'),
                'meli_shipping_sender_id': str(data.get('sender_id')),
                'meli_shipping_receiver_id': str(data.get('receiver_id')),
                'meli_shipping_service_id': str(data.get('service_id')),
                'meli_shipping_priority_class_id': data.get('priority_class', {}).get('id'),
                'meli_shipping_last_updated': self.parse_meli_datetime(data.get('last_updated')),
                'meli_shipping_date_created': self.parse_meli_datetime(data.get('date_created')),
                'meli_shipping_date_first_printed': self.parse_meli_datetime(data.get('date_first_printed')),
                'meli_shipping_created_by': data.get('created_by'),
                'meli_shipping_marketplace': data.get('market_place'),
                'meli_shipping_site_id': data.get('site_id'),
                # Shipping Option
                'meli_shipping_option_id': shipping_option.get('id'),
                'meli_shipping_option_name': shipping_option.get('name'),
                'meli_shipping_option_cost': shipping_option.get('cost'),
                'meli_shipping_option_list_cost': shipping_option.get('list_cost'),
                'meli_shipping_cost': shipping_option.get('list_cost') - shipping_option.get('cost'),
                # Receiver Address
                'meli_receiver_city': receiver.get('city', {}).get('name'),
                'meli_receiver_state': receiver.get('state', {}).get('name'),
                'meli_receiver_country': receiver.get('country', {}).get('name'),
                'meli_receiver_zip_code': receiver.get('zip_code'),
                'meli_receiver_street_name': receiver.get('street_name'),
                'meli_receiver_street_number': receiver.get('street_number'),
                'meli_receiver_latitude': receiver.get('latitude'),
                'meli_receiver_longitude': receiver.get('longitude'),

                # Sender Address
                'meli_sender_city': sender.get('city', {}).get('name'),
                'meli_sender_state': sender.get('state', {}).get('name'),
                'meli_sender_country': sender.get('country', {}).get('name'),
                'meli_sender_zip_code': sender.get('zip_code'),
                'meli_sender_street_name': sender.get('street_name'),
                'meli_sender_street_number': sender.get('street_number'),
                'meli_sender_latitude': sender.get('latitude'),
                'meli_sender_longitude': sender.get('longitude'),                
            })
            if data.get('status')=='delivered':
                order.action_confirm_delivery()
                if order.instance_id.allow_send_auto_invoice:
                    if order.meli_shipping_logistic_type == 'fulfillment':
                        if not order.meli_autoinvoicing_sent:
                            _logger.info("Enviando mensaje de autoinvoicing al cliente...")
                            order.meli_send_message_to_customer()
                            order.meli_autoinvoicing_sent = True
        return True
        
    def action_get_customer_details(self):
        def find_city_record(city_name):
            def normalize(text):
                return ''.join(
                    c for c in unicodedata.normalize('NFD', text)
                    if unicodedata.category(c) != 'Mn'
                ).lower().strip()

            normalized_input = normalize(city_name)
            all_cities = self.env['res.city'].search([])
            for city in all_cities:
                if normalize(city.name) == normalized_input:
                    return city
            return False
        for order in self:
            if not order.meli_shipping_id or not order.instance_id:
                continue

            # Si no hay datos de dirección, obtenerlos desde la API
            if not order.meli_receiver_street_name:
                shipment_url = f"https://api.mercadolibre.com/shipments/{order.meli_shipping_id}"
                headers = {
                    'Authorization': f'Bearer {order.instance_id.meli_access_token}'
                }
                try:
                    response = requests.get(shipment_url, headers=headers)
                    if response.status_code == 200:
                        shipment = response.json()
                        receiver = shipment.get('receiver_address', {})
                        order.write({
                            'meli_receiver_street_name': receiver.get('street_name', ''),
                            'meli_receiver_street_number': receiver.get('street_number', ''),
                            'meli_receiver_city': receiver.get('city', {}).get('name', ''),
                            'meli_receiver_state': receiver.get('state', {}).get('name', ''),
                            'meli_receiver_country': receiver.get('country', {}).get('name', ''),
                            'meli_receiver_zip_code': receiver.get('zip_code', ''),
                        })
                    else:
                        _logger.warning(f"No se pudo obtener el envío {order.meli_shipping_id}: {response.text}")
                except Exception as e:
                    _logger.exception(f"Error al consultar el shipment de MercadoLibre: {e}")
                    continue

            # Buscar ciudad normalizada
            city_record = find_city_record(order.meli_receiver_city)

            # Extraer campos desde city
            country_id = city_record.state_id.country_id.id if city_record and city_record.state_id and city_record.state_id.country_id else False
            state_id = city_record.state_id.id if city_record and city_record.state_id else False
            zip_code = city_record.zipcode if city_record and city_record.zipcode else order.meli_receiver_zip_code

            # Buscar o crear partner
            partner = self.env['res.partner'].search([
                ('nickname', '=', order.meli_buyer_nickname),
                ('instance_id', '=', order.instance_id.id)
            ], limit=1)

            partner_vals = {
                'name': f"{order.meli_buyer_first_name or ''} {order.meli_buyer_last_name or ''}".strip(),
                'nickname': order.meli_buyer_nickname,
                'street': order.meli_receiver_street_name,
                'street2': order.meli_receiver_street_number,
                'country_id': country_id,
                'state_id': state_id,
                'city': city_record.name if city_record else order.meli_receiver_city,
                'city_id': city_record.id if city_record else False,
                'zip': zip_code,
                #'l10n_latam_identification_type_id': self.env.ref('l10n_latam_base.it_type_dni').id,
                'vat': '',  # aún no lo tienes
                'instance_id': order.instance_id.id
            }

            if partner:
                partner.write(partner_vals)
                _logger.info(f"Partner actualizado: {partner.name} ({order.meli_buyer_nickname})")
            else:
                partner = self.env['res.partner'].create(partner_vals)
                _logger.info(f"Partner creado: {partner.name} ({order.meli_buyer_nickname})")

            # Asignar el partner a la orden
            if not order.partner_id:
                order.partner_id = partner

        return True

    @api.model
    def process_label(self, shipping_id, meli_code):    
        acces_token = self.env['sale.order'].search([('meli_order_id', '=', meli_code)], limit=1).instance_id.meli_access_token

        if acces_token and shipping_id:
            pdf_url = self.get_shipping_label_content(shipping_id, acces_token)

            if pdf_url:
                # Devuelve el contenido binario del PDF
                return pdf_url
        return None

    def get_shipping_label_content(self, shipment_id: str, access_token: str):
        """Obtiene el contenido del PDF para un shipment_id específico."""
        _logger.info(f"[START] Obteniendo la etiqueta de envío para el shipment_id {shipment_id}")

        url = f"https://api.mercadolibre.com/shipment_labels?shipment_ids={shipment_id}&savePdf=Y"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        _logger.info(f"[INFO] URL: {url}")
        _logger.info(f"[INFO] Headers: {headers}")

        try:
            response = requests.get(url, headers=headers)
            _logger.info(f"[SUCCESS] Solicitud enviada. Código de estado: {response.status_code}")
            response.raise_for_status()


            if response.status_code == 200:
                _logger.info("[SUCCESS] Etiqueta de envío obtenida con éxito.")
                return response.content  # Devuelve el contenido binario del PDF
            else:
                _logger.warning(f"[WARNING] Respuesta inesperada: {response.status_code}")
                return None
        except requests.RequestException as e:
            _logger.error(f"[ERROR] Error al obtener la etiqueta de envío: {str(e)}")
            return None
    def print_guides(self):
        """Acción personalizada que se ejecutará desde el menú."""
        pdfs = []

        for order in self:
            _logger.info(f"Procesando la orden {order.name}...")
            pdf_binary = self.process_label(order.meli_shipping_id, order.meli_order_id)
            if pdf_binary:
                pdfs.append(pdf_binary)

        if pdfs:
            # Combina todos los PDFs en uno solo
            combined_pdf = self.combine_pdfs(pdfs)

            # Guarda el PDF combinado en ir.config_parameter
            encoded_combined_pdf = base64.b64encode(combined_pdf).decode('utf-8')
            self.env['ir.config_parameter'].sudo().set_param('current_shipping_label', encoded_combined_pdf)

            # Redirige al usuario al controlador para descargar el PDF combinado
            return {
                'type': 'ir.actions.act_url',
                'url': '/custom/view_pdf_label',
                'target': 'new',
            }
        else:
            # Notifica al usuario si no se pudieron generar etiquetas
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': 'No se pudieron generar las etiquetas de envío.',
                    'sticky': False,
                },
            }

    def combine_pdfs(self, pdf_binaries):
        """Combina múltiples PDFs en uno solo."""
        merger = PdfMerger()
        for pdf_binary in pdf_binaries:
            pdf_stream = io.BytesIO(pdf_binary)
            merger.append(pdf_stream)

        output_stream = io.BytesIO()
        merger.write(output_stream)
        merger.close()

        return output_stream.getvalue()
    
    @api.model
    def total_ventas_mercadolibre(self):
        today = fields.Date.today()
        first_day = today.replace(day=1)
        last_day = (first_day + relativedelta(months=1)) - relativedelta(days=1)

        orders = self.search([
            #('store_type', '=', 'mercadolibre'),
            ('date_order', '>=', first_day),
            ('date_order', '<=', last_day)
        ])

        total_sales = sum(orders.mapped('amount_total'))

        currency = orders[:1].currency_id  # Toma la moneda del primer pedido
        currency_symbol = currency.symbol if currency else '$'
        return {
            'total_sales': round(total_sales, 2),
            'currency_symbol': currency_symbol
        }
    
    @api.model
    def mes_pasado_ventas_mercadolibre(self):
        today = fields.Date.today()
        first_day_current_month = today.replace(day=1)
        first_day_last_month = first_day_current_month - relativedelta(months=1)
        last_day_last_month = first_day_current_month - relativedelta(days=1)

        orders = self.search([
            #('store_type', '=', 'mercadolibre'),
            ('date_order', '>=', first_day_last_month),
            ('date_order', '<=', last_day_last_month)
        ])

        total_sales = sum(orders.mapped('amount_total'))

        return {
            'total_sales': round(total_sales, 2)
        }

    def get_customer_forecast_data(self):
        _logger.info("Iniciando forecast de nuevos clientes...")

        # Buscar fechas de primera orden por cliente
        query = """
            SELECT MIN(date_order::date) as first_order_date
            FROM sale_order
            WHERE state IN ('sale', 'done')
              AND partner_id IS NOT NULL
            GROUP BY partner_id
            ORDER BY first_order_date
        """
        self._cr.execute(query)
        rows = self._cr.fetchall()

        if not rows:
            _logger.warning("No se encontraron datos de primeros pedidos de clientes.")
            return {'labels': [], 'datasets': []}

        # Agrupar por fecha
        date_counts = {}
        for (first_date,) in rows:
            date_counts[first_date] = date_counts.get(first_date, 0) + 1

        df = pd.DataFrame(list(date_counts.items()), columns=["ds", "y"])
        df = df.sort_values("ds")

        if df["ds"].nunique() < 2:
            _logger.warning("No hay suficientes fechas distintas para entrenar modelo de clientes.")
            return {'labels': [], 'datasets': []}

        # Entrenar modelo
        model = Prophet()
        model.fit(df)

        # Predecir 30 días
        future = model.make_future_dataframe(periods=30)
        forecast = model.predict(future)

        labels = forecast['ds'].dt.strftime('%Y-%m-%d').tolist()
        real = forecast['yhat'][:-30].tolist()
        pred = forecast['yhat'][-30:].tolist()

        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Clientes Nuevos Históricos',
                    'data': real + [None] * 30,
                    'borderColor': 'rgb(54, 162, 235)',
                },
                {
                    'label': 'Clientes Nuevos Predichos',
                    'data': [None] * len(real) + pred,
                    'borderColor': 'rgb(255, 99, 132)',
                    'borderDash': [5, 5],
                }
            ]
        }

    def action_confirm(self):
        _logger.info("DENTRO DE LA FUNCION CONFIRMAR ORDEN DE VENTA")
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            tmpl_ids = {l.product_id.product_tmpl_id.id for l in order.order_line if l.product_id}
            for tmpl in self.env['product.template'].browse(list(tmpl_ids)):
                try:
                    if not tmpl.meli_product_id or not tmpl.instance_id:
                        _logger.info("Saltando template %s (sin ML ID o sin instancia)", tmpl.id)
                        continue
                    tmpl._update_stock_mercadolibre()
                except Exception as e:
                    _logger.warning("No se pudo actualizar stock ML del template %s: %s", tmpl.id, e)
        return res

class StockMove(models.Model):
    _inherit = 'stock.move'

    def action_done(self):
        res = super().action_done()
        for move in self:
            product_tmpl = move.product_id.product_tmpl_id
            if hasattr(product_tmpl, '_update_stock_mercadolibre'):
                product_tmpl._update_stock_mercadolibre()
        return res

class MeliOrderMediation(models.Model):
    _name = 'meli.order.mediation'
    _description = 'Meli Order Mediation'

    order_id = fields.Many2one('sale.order', string="Sale Order")
    meli_mediation_id = fields.Char(string="Mediation ID")


class MeliOrderItem(models.Model):
    _name = 'meli.order.item'
    _description = 'Meli Order Item'

    order_id = fields.Many2one('sale.order', string="Sale Order")
    meli_item_id = fields.Char(string="Item ID")
    meli_title = fields.Char(string="Title")
    meli_category_id = fields.Char(string="Category ID")
    meli_variation_id = fields.Char(string="Variation ID")
    meli_warranty = fields.Char(string="Warranty")
    meli_condition = fields.Char(string="Condition")
    meli_quantity = fields.Integer(string="Quantity")
    meli_measure = fields.Char(string="Measure")
    meli_value = fields.Float(string="Requested Quantity Value")
    meli_unit_price = fields.Float(string="Unit Price")
    meli_full_unit_price = fields.Float(string="Full Unit Price")
    meli_currency_id = fields.Char(string="Currency")
    meli_sale_fee = fields.Float(string="Sale Fee")
    meli_listing_type_id = fields.Char(string="Listing Type ID")


class MeliOrderPayment(models.Model):
    _name = 'meli.order.payment'
    _description = 'Meli Order Payment'

    order_id = fields.Many2one('sale.order', string="Sale Order")
    meli_payment_id = fields.Char(string="Payment ID")
    meli_payer_id = fields.Char(string="Payer ID")
    meli_collector_id = fields.Char(string="Collector ID")
    meli_reason = fields.Char(string="Reason")
    meli_site_id = fields.Char(string="Site ID")
    meli_payment_method_id = fields.Char(string="Payment Method")
    meli_currency_id = fields.Char(string="Currency")
    meli_installments = fields.Integer(string="Installments")
    meli_issuer_id = fields.Char(string="Issuer ID")
    meli_operation_type = fields.Char(string="Operation Type")
    meli_payment_type = fields.Char(string="Payment Type")
    meli_status = fields.Char(string="Status")
    meli_status_detail = fields.Char(string="Status Detail")
    meli_transaction_amount = fields.Float(string="Transaction Amount")
    meli_transaction_amount_refunded = fields.Float(string="Transaction Amount Refunded")
    meli_taxes_amount = fields.Float(string="Taxes Amount")
    meli_shipping_cost = fields.Float(string="Shipping Cost")
    meli_coupon_amount = fields.Float(string="Coupon Amount")
    meli_overpaid_amount = fields.Float(string="Overpaid Amount")
    meli_total_paid_amount = fields.Float(string="Total Paid Amount")
    meli_date_approved = fields.Datetime(string="Date Approved")
    meli_date_created = fields.Datetime(string="Date Created")
    meli_date_last_modified = fields.Datetime(string="Date Last Modified")
    meli_marketplace_fee = fields.Float(string="Marketplace Fee")

class SaleMeliTag(models.Model):
    _name = 'sale.meli.tag'
    _description = 'MercadoLibre Tag para Venta'

    name = fields.Char(required=True, index=True)


class SaleMeliInternalTag(models.Model):
    _name = 'sale.meli.internal.tag'
    _description = 'MercadoLibre Internal Tag para Venta'

    name = fields.Char(required=True, index=True)


class SaleMeliContextFlow(models.Model):
    _name = 'sale.meli.context.flow'
    _description = 'MercadoLibre Context Flow para Venta'

    name = fields.Char(required=True, index=True)

# Substatus History
class SaleMeliShippingSubstatus(models.Model):
    _name = 'sale.meli.shipping.substatus'
    _description = "MercadoLibre Shipping Substatus"

    order_id = fields.Many2one('sale.order', string="Sale Order")
    date = fields.Datetime("Date", help="Date when the substatus was registered.")
    substatus = fields.Char("Substatus", help="Shipping substatus (e.g., packed, in_warehouse).")
    status = fields.Char("Status", help="Main status (e.g., pending, ready_to_ship).")

# Shipping Items
class SaleMeliShippingItem(models.Model):
    _name = 'sale.meli.shipping.item'
    _description = "MercadoLibre Shipping Item"

    order_id = fields.Many2one('sale.order', string="Sale Order")
    item_id = fields.Char("Item ID", help="Item ID in MercadoLibre.")
    description = fields.Char("Description", help="Item description.")
    quantity = fields.Integer("Quantity", help="Number of units.")
    dimensions = fields.Char("Dimensions", help="Dimensions in format LxWxH,Weight.")
    sender_id = fields.Char("Sender ID", help="Sender ID of the item.")
    user_product_id = fields.Char("User Product ID", help="User-specific product ID.")
    origin = fields.Char("Origin", help="Origin of dimensions (e.g., 'fd').")

# Tags (Many2many)
class SaleMeliShippingTag(models.Model):
    _name = 'sale.meli.shipping.tag'
    _description = 'MercadoLibre Shipping Tag'
    name = fields.Char(required=True)

# Item Types (Many2many)
class SaleMeliShippingItemType(models.Model):
    _name = 'sale.meli.shipping.item.type'
    _description = 'MercadoLibre Shipping Item Type'
    name = fields.Char(required=True)
    