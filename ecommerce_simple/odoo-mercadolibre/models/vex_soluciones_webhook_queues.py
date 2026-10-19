from odoo import models, fields
import json
import logging
import requests
from datetime import datetime
from dateutil.parser import isoparse

_logger = logging.getLogger(__name__)
class VexSolucionesWebhookQueues(models.Model):
    _name = 'vex.webhook.queue'
    _description = 'Cola de Webhook de Vex Soluciones'
    _order = 'create_date desc'
    _rec_name = 'meli_id'

    meli_id = fields.Char(string='ID de Mercado Libre', required=True, help="ID del recurso de Mercado Libre relacionado con el webhook")
    event_type = fields.Selection([
        ('orders_v2', 'Ordenes'),
        ('items', 'Productos'),
        ('questions', 'Preguntas'),
        ('answers', 'Respuestas'),
        ('users', 'Usuarios'),
        ('feedback', 'Calificaciones'),
        ('claims', 'Reclamos'),
        ('messages', 'Mensajes'),
        ('payments', 'Pagos'),
        ('shipments', 'Envios'),
        ('inventory_changes', 'Cambios de inventario'),
        ('invoice', 'Facturación'),
        ('dispute_message', 'Dispute Messages'),
        ('return', 'Returns'),
        ('payout', 'Payouts'),
        ('application', 'Applications'),
        ('fbm_stock_operations', 'FBM Stock Operations'),
        ('public_candidates', 'Public Candidates'),
        ('public_offers', 'Public Offers'),
        ('items_prices', 'Item Prices'),
        ('user-products-families', 'User Product Families'),
        ('post_purchase', 'Post Purchase'),        
        ('catalog_suggestions', 'Catalog Suggestions'),
        ('orders_feedback', 'Orders Feedback'),
        ('stock-locations', 'Stock Locations'),
        ('catalog_item_competition_status', 'Catalog Item Competition Status'),
        ('price_suggestions', 'Price Suggestions')
    ], string='Tipo de Evento', required=True, help="Tipo de evento enviado por MercadoLibre")

    create_date = fields.Datetime(string='Fecha de Creación', default=fields.Datetime.now)
    write_date = fields.Datetime(string='Fecha de Modificación', default=fields.Datetime.now)   
    processed = fields.Boolean(string='Procesado', default=False, help="Indica si el webhook ha sido procesado")
    error_message = fields.Text(string='Mensaje de Error', help="Mensaje de error si el procesamiento falla")
    instance_id = fields.Many2one('vex.instance', string='Instancia', required=True, help="Instancia de Vex Soluciones a la que pertenece el webhook")
    priority = fields.Integer(string='Prioridad', default=0, help="Prioridad del webhook en la cola, menor valor indica mayor prioridad")
    retry_count = fields.Integer(string='Contador de Reintentos', default=0, help="Número de veces que se ha intentado procesar el webhook")
    max_retries = fields.Integer(string='Máximo de Reintentos', default=3, help="Número máximo de reintentos permitidos para procesar el webhook")
    payload = fields.Text(string='Payload', help="Datos del webhook en formato JSON")
    status = fields.Selection([
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('error', 'Error'),
    ], string='Estado', default='pending', help="Estado actual del webhook en la cola")
    response = fields.Text(string='Respuesta', help="Respuesta del procesamiento del webhook, si aplica")


    # def _get_or_create_partner_from_meli(self, buyer_info, instance_id, headers):
    #     nickname = buyer_info.get("nickname")
    #     partner = self.env['res.partner'].search([
    #         ('name', '=', nickname),
    #         ('instance_id', '=', instance_id.id)
    #     ], limit=1)

    #     if not partner:
    #         buyer_id = buyer_info.get("id")
    #         url = f"https://api.mercadolibre.com/users/{buyer_id}"
    #         response = requests.get(url, headers=headers)
    #         if response.status_code == 200:
    #             buyer_data = response.json()
    #             nickname = buyer_data.get("nickname")
    #             partner = self.env['res.partner'].create({
    #                 'name': f"{buyer_data.get('first_name', nickname)} {buyer_data.get('last_name', '')}",
    #                 'nickname': nickname,
    #                 'meli_user_id': buyer_id,
    #                 #'l10n_latam_identification_type_id': 1,
    #                 'instance_id': instance_id.id,
    #                 'server_meli': True
    #             })
    #             _logger.info(f"Created partner for {nickname} ({buyer_id})")
    #     return partner

    # def _get_or_create_product(self, meli_item_id, instance_id, headers):
    #     product_tmpl = self.env['product.template'].search([
    #         ('default_code', '=', meli_item_id),
    #         ('instance_id', '=', instance_id.id),
    #         ('active', '=', True)
    #     ], limit=1)

    #     if not product_tmpl:
    #         item_url = f"https://api.mercadolibre.com/items/{meli_item_id}"
    #         response = requests.get(item_url, headers=headers)
    #         if response.status_code == 200:
    #             item_data = response.json()
    #             attribute_value_tuples = []
    #             for attr in item_data.get('attributes', []):
    #                 if attr.get('id') and attr.get('value_name'):
    #                     attribute_value_tuples.append((0, 0, {
    #                         'attribute_id': self.env['product.attribute'].search([('name', '=', attr['name'])], limit=1).id,
    #                         'value_ids': [(6, 0, [
    #                             self.env['product.attribute.value'].search([('name', '=', attr['value_name'])], limit=1).id
    #                         ])]
    #                     }))

    #             values = {
    #                 #'categ_id': instance_id.product_categ_id.id if instance_id.product_categ_id else False,
    #                 'name': item_data['title'],
    #                 'list_price': item_data['price'],
    #                 'mercado_libre_price': item_data['price'],
    #                 'meli_code': item_data['id'],
    #                 'default_code': item_data['id'],
    #                 'server_meli': True,
    #                 'detailed_type': 'product',
    #                 'image_1920': item_data.get('thumbnail'),
    #                 'ml_reference': item_data['id'],
    #                 'ml_publication_code': item_data['id'],
    #                 'meli_category_code': item_data['category_id'],
    #                 'meli_status': item_data['status'],
    #                 #'attribute_line_ids': attribute_value_tuples,
    #                 'sku_id': False,
    #                 'listing_type_id': item_data['listing_type_id'],
    #                 'condition': item_data['condition'],
    #                 'permalink': item_data['permalink'],
    #                 'thumbnail': item_data['thumbnail'],
    #                 'buying_mode': item_data['buying_mode'],
    #                 'inventory_id': item_data.get('inventory_id'),
    #                 'action_export': 'edit',
    #                 'instance_id': instance_id.id,
    #                 #'stock_type': instance_id.stock_type,
    #                 #'upc': next((attr['value_name'] for attr in item_data.get('attributes', []) if attr['id'] == 'GTIN'), None),
    #                 'store_type': 'mercadolibre',
    #                 'market_fee': 0.0
    #             }
    #             product_tmpl = self.env['product.template'].create(values)

    #     if product_tmpl:
    #         product = self.env['product.product'].search([
    #             ('product_tmpl_id', '=', product_tmpl.id),
    #             ('active', '=', True)
    #         ], limit=1)
    #         return product_tmpl, product

    #     raise ValueError(f"Product {meli_item_id} could not be created or found.")
        
    # def _build_order_lines(self, items, instance_id, headers):
    #     order_lines = []
    #     for item in items:
    #         product_tmpl, product = self._get_or_create_product(item['item']['id'], instance_id, headers)
    #         if not product:
    #             raise ValueError(f"No product for item {item['item']['id']}")

    #         line = {
    #             'product_id': product.id,
    #             'product_template_id': product_tmpl.id,
    #             'name': product_tmpl.name,
    #             'product_uom_qty': item['quantity'],
    #             'price_unit': item['unit_price'],
    #             'tax_id': [(5, 0, 0)],
    #             'display_type': False
    #         }
    #         order_lines.append((0, 0, line))
    #     return order_lines

    # def _categorize_order_status(self, json_order):
    #     tags = json_order.get('tags', [])
    #     payments = json_order.get('payments', [])
    #     approved = sum(1 for p in payments if p.get('status') == 'approved')
    #     charged_back = sum(1 for p in payments if p.get('status') == 'charged_back' and p.get('status_detail') == 'reimbursed')

    #     if approved >= 1 and 'paid' in tags and 'delivered' in tags:
    #         return 'Completada', True
    #     if json_order.get('status') == 'cancelled':
    #         return 'Canceled', False
    #     if approved >= 1 and 'paid' in tags and 'not_delivered' in tags:
    #         return 'Pending', False
    #     if json_order.get('status') == 'partially_refunded':
    #         return 'Partially Refunded', False
    #     if approved == 0 and charged_back >= 1:
    #         return 'Reimbursed', False
    #     if json_order.get('fulfilled') and 'no_shipping' in tags:
    #         return 'Completada', True
    #     return 'No Pagada', False

    # def process_queue_orders(self):
    #     orders = self.search([('event_type', '=', 'orders_v2'), ('processed', '=', False)], limit=50)
    #     for record in orders:
    #         try:
    #             instance = record.instance_id
    #             meli_order_id = record.meli_id
    #             headers = {
    #                 'Content-Type': 'application/x-www-form-urlencoded',
    #                 'Authorization': f'Bearer {instance.meli_access_token}'
    #             }

    #             existing_order = self.env['sale.order'].search([
    #                 ('meli_code', '=', meli_order_id),
    #                 ('instance_id', '=', instance.id)
    #             ], limit=1)
    #             if existing_order:
    #                 record.write({
    #                     'status': 'completed',
    #                     'processed': True,
    #                     'response': 'Ya existía la orden'
    #                 })
    #                 continue

    #             url = f"https://api.mercadolibre.com/orders/{meli_order_id}"
    #             response = requests.get(url, headers=headers)
    #             if response.status_code != 200:
    #                 raise Exception(f"Error al obtener la orden {meli_order_id} desde MercadoLibre")

    #             json_order = response.json()
    #             buyer_info = json_order.get('buyer', {})

    #             partner = self._get_or_create_partner_from_meli(buyer_info, instance, headers)

    #             shipping_id, shipping_type, shipping_status = '', '', 'Not Delivered'
    #             if json_order.get('shipping', {}).get('id'):
    #                 shipment_url = f"https://api.mercadolibre.com/shipments/{json_order['shipping']['id']}"
    #                 shipment_response = requests.get(shipment_url, headers=headers)
    #                 if shipment_response.status_code == 200:
    #                     shipment_data = shipment_response.json()
    #                     shipping_id = shipment_data.get('id')
    #                     shipping_type = shipment_data.get('logistic_type', '')
    #                     shipping_status = shipment_data.get('status', '')
    #                     _logger.info(f"Shipping data:{shipment_data}")
    #                     shipping_options = shipment_data.get('shipping_option', [])
    #                     _logger.info(f"Shipping options: {shipping_options}")
    #                     if shipping_options:
    #                         list_cost = shipping_options.get('list_cost', 0.0)
    #                         cost = shipping_options.get('cost', 0.0)
    #                         shipping_cost = list_cost - cost
    #                     else:
    #                         shipping_cost = 0.0

    #             order_lines = self._build_order_lines(json_order.get('order_items', []), instance, headers)
    #             order_status, order_is_closed = self._categorize_order_status(json_order)
    #             _logger.info(json_order)
    #             order_vals = {
    #                 'meli_code': json_order['id'],
    #                 'partner_id': partner.id,
    #                 'date_order': isoparse(json_order['date_created']).replace(tzinfo=None),
    #                 'state': 'sale',
    #                 'server_meli': True,
    #                 'shipping_id': shipping_id,
    #                 'shipping_type': shipping_type,
    #                 'shipping_status': shipping_status,
    #                 'order_line': order_lines,
    #                 'total_paid_amount': json_order.get('paid_amount', 0.0),
    #                 'shipping_cost': shipping_cost,
    #                 'marketplace_fee': sum(p.get('marketplace_fee', 0.0) for p in json_order.get('payments', [])),
    #                 'order_status': order_status,
    #                 'order_is_closed': order_is_closed,
    #                 'instance_id': instance.id,
    #                 'tags': ','.join(json_order.get('tags', [])),
    #                 'listing_type_id': json_order['order_items'][0].get('listing_type_id', '') if json_order.get('order_items') else '',

    #             }
    #             _logger.info(order_vals)

    #             self.env['sale.order'].create(order_vals)

    #             record.write({
    #                 'status': 'completed',
    #                 'processed': True,
    #                 'retry_count': 0,
    #                 'response': 'Orden creada exitosamente'
    #             })
    #             _logger.info(f"[QUEUE] Orden {meli_order_id} procesada exitosamente.")

    #         except Exception as e:
    #             record.retry_count += 1
    #             new_status = 'failed' if record.retry_count >= record.max_retries else 'pending'
    #             record.write({
    #                 'status': new_status,
    #                 'error_message': str(e),
    #                 'response': str(e)
    #             })
    #             _logger.error(f"[QUEUE] Error procesando orden {record.meli_id}: {e}")

    # def update_event_type_from_payload(self):
    #     """Actualiza el campo event_type basado en el campo 'topic' del payload JSON."""
    #     records_to_update = self.search([('payload', '!=', False), ('event_type', '=', False)])
    #     updated_count = 0

    #     for record in records_to_update:
    #         try:
    #             payload = json.loads(record.payload)
    #             topic = payload.get('topic')
    #             if topic:
    #                 record.write({'event_type': topic})
    #                 updated_count += 1
    #         except Exception as e:
    #             _logger.error(f"[UPDATE_EVENT_TYPE] Error procesando payload en registro {record.id}: {e}")
        
    #     _logger.info(f"[UPDATE_EVENT_TYPE] Total de registros actualizados: {updated_count}")



    def process_queue_orders(self):
        """Procesa los registros de la cola de webhooks relacionados con órdenes."""
        orders = self.search([('event_type', '=', 'orders_v2'), ('processed', '=', False)], limit=50)
        for line in orders:
            try:
                if not line.meli_id:
                    line.write({'status': 'error', 'result': 'Falta descripción'})
                    continue
                _logger.info(f"Procesando orden: {line.meli_id}")
                meli_partner_id = self.env.ref('odoo-mercadolibre.res_partner_cliente_meli').id
                instance = line.instance_id
                instance.get_access_token()
                meli_order_id = line.meli_id
                if not meli_order_id:
                    line.write({'status': 'error', 'result': 'ID de orden no encontrado en JSON', 'start_date': fields.Datetime.now(), 'end_date': fields.Datetime.now()})
                    continue

                # Aquí puedes agregar la lógica para procesar la orden
                sale_order = self.env['sale.order'].search([('meli_order_id', '=', meli_order_id)], limit=1)
                if sale_order:
                    sale_order.action_get_details()  # Actualizar detalles de la orden si es necesario
                    sale_order.action_get_shipping_details()
                    sale_order.action_get_customer_details()
                    sale_order.action_copy_datetime_to_date()
                else:
                    # Crear una nueva orden de venta
                    sale_order = self.env['sale.order'].create({
                        'meli_order_id': meli_order_id,
                        'instance_id': instance.id,
                        'marketplace_ids': [(4, self.env.ref('odoo-mercadolibre.vex_marketplace_mercadolibre').id)],
                        'partner_id': meli_partner_id,  # Asignar el cliente
                        # Agregar más campos según sea necesario
                    })
                    sale_order.action_get_details()
                    sale_order.action_get_shipping_details()
                    sale_order.action_get_customer_details()
                    sale_order.action_copy_datetime_to_date()
                # Por ejemplo, crear un registro de venta o actualizar uno existente
                line.write({
                    'status': 'completed',
                    'processed': True,
                    'retry_count': 0,
                    'response': 'Orden creada exitosamente'
                })

            except Exception as e:
                line.retry_count += 1
                _logger.error(f"❌ Error procesando orden {line.meli_id}: {str(e)}")
                line.write({
                    'status': 'error',
                    #'processed': True,
                    'retry_count': line.retry_count,
                    'response': str(e)
                })


    def process_queue_product(self):
        """Procesa los registros de la cola de webhooks relacionados con órdenes."""
        orders = self.search([('event_type', '=', 'items'), ('processed', '=', False)], limit=50)
        for line in orders:
            try:
                if not line.meli_id:
                    line.write({'status': 'error', 'result': 'Falta descripción'})
                    continue
                _logger.info(f"Procesando orden: {line.meli_id}")
                meli_partner_id = self.env.ref('odoo-mercadolibre.res_partner_cliente_meli').id
                instance = line.instance_id
                instance.get_access_token()
                meli_product_id = line.meli_id
                if not meli_product_id:
                    line.write({'status': 'error', 'result': 'ID de orden no encontrado en JSON', 'start_date': fields.Datetime.now(), 'end_date': fields.Datetime.now()})
                    continue

                # Aquí puedes agregar la lógica para procesar la orden
                product_id = self.env['product.template'].search([('meli_product_id', '=', meli_product_id)], limit=1)
                if product_id:
                    product_id.action_get_details()  # Actualizar detalles de la orden si es necesario
                else:
                    # Crear una nueva orden de venta
                    product_id = self.env['product.template'].create({
                        'meli_product_id': meli_product_id,
                        'instance_id': instance.id,
                        'marketplace_ids': [(4, self.env.ref('odoo-mercadolibre.vex_marketplace_mercadolibre').id)],
                        # Agregar más campos según sea necesario
                    })
                    product_id.action_get_details()
                    product_id.set_image_from_meli()
                # Por ejemplo, crear un registro de venta o actualizar uno existente

                line.write({
                    'status': 'completed',
                    'processed': True,
                    'retry_count': 0,
                    'response': 'Orden creada exitosamente'
                })

            except Exception as e:
                _logger.error(f"❌ Error procesando Producto {line.meli_id}: {str(e)}")
                line.write({
                    'status': 'error',
                    #'processed': True,
                    'retry_count': line.retry_count,
                    'response': str(e)
                })
    
    def process_queue_questions(self):
        """Procesa los registros de la cola de webhooks relacionados con órdenes."""
        questions = self.search([('event_type', '=', 'questions'), ('processed', '=', False)], limit=50)
        for line in questions:
            try:
                if not line.meli_id:
                    line.write({'status': 'error', 'result': 'Falta descripción'})
                    continue
                _logger.info(f"Procesando question: {line.meli_id}")
                instance = line.instance_id
                instance.get_access_token()
                access_token = instance.meli_access_token
                meli_question_id = line.meli_id
                if not meli_question_id:
                    line.write({'status': 'error', 'result': 'ID de orden no encontrado en JSON', 'start_date': fields.Datetime.now(), 'end_date': fields.Datetime.now()})
                    continue
                

                # Aquí puedes agregar la lógica para procesar la orden
                question_id = self.env['vex.meli.questions'].search([('meli_id', '=', meli_question_id)], limit=1)
                if question_id:
                    product_id = self.env['product.template'].search([('id','=',question_id.product_id.id)])
                    product_id.action_sync_questions()  # Actualizar detalles de la orden si es necesario
                    line.write({
                        'status': 'completed',
                        'processed': True,
                        'retry_count': 0,
                        'response': 'Question creada exitosamente'
                    })                    
                else:
                    url = f"https://api.mercadolibre.com/questions/{meli_question_id}"
                    headers = {'Authorization': f'Bearer {access_token}'}
                    response = requests.get(url, headers=headers)

                    if response.status_code != 200:

                        line.write({
                            'status': 'failed',
                            'response': f"API ML {response.status_code} - {response.text}",

                        })
                        continue
                    data = response.json()
                    meli_item_id = data.get('item_id')
                    product_id = self.env['product.template'].search([('meli_product_id','=',meli_item_id)])
                    product_id.action_sync_questions()  # Actualizar detalles de la orden si es necesario                        
                    # Por ejemplo, crear un registro de venta o actualizar uno existente

                    line.write({
                        'status': 'completed',
                        'processed': True,
                        'retry_count': 0,
                        'response': 'Question creada exitosamente'
                    })

            except Exception as e:
                _logger.error(f"❌ Error procesando Producto {line.meli_id}: {str(e)}")
                line.write({
                    'status': 'failed',
                    #'processed': True,
                    'retry_count': line.retry_count,
                    'response': str(e)
                })        
