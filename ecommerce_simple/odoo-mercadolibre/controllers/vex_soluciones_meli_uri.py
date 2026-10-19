# controllers/main.py
from odoo import http
from odoo.http import request
import logging
import requests
import json

_logger = logging.getLogger(__name__)

class MeliLoginController(http.Controller):

    @http.route('/meli_login/ceralfasa', type='http', auth='public', website=True)
    def meli_login_ceralfasa_callback(self, **kwargs):
        code = kwargs.get('code')
        if not code:
            return "No se recibió el código de autorización"

        _logger.info(f"Recibido código de autorización: {code}")

        # Aquí podrías buscar el client_id y client_secret desde la config o db
        client_id = '4753009464781172'
        client_secret = 'hHMIm7TKCXJl0y6iVgAmMK2iG6b1eLKr'
        redirect_uri = 'https://ceralfa.odoo.com/meli_login/ceralfasa'

        try:
            # Hacer la petición POST para obtener el access_token
            response = requests.post(
                'https://api.mercadolibre.com/oauth/token',
                data={
                    'grant_type': 'authorization_code',
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'code': code,
                    'redirect_uri': redirect_uri,
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            result = response.json()

            if response.status_code == 200:
                access_token = result.get('access_token')
                _logger.info(f"Token de acceso obtenido: {access_token}")
                return f"Autenticación exitosa. Token: {access_token}"
            else:
                _logger.error(f"Error en autenticación: {result}")
                return f"Error al obtener el token: {result}"

        except Exception as e:
            _logger.exception("Excepción al obtener el token de acceso")
            return f"Excepción: {str(e)}"
        
    @http.route('/meli_login/cere', type='http', auth='public', website=True)
    def meli_login_cere_callback(self, **kwargs):
        code = kwargs.get('code')
        if not code:
            return "No se recibió el código de autorización"

        _logger.info(f"Recibido código de autorización: {code}")

        # Aquí podrías buscar el client_id y client_secret desde la config o db
        client_id = '2853407314226899'
        client_secret = 'WNnSSSlugQTeFB8vqXdFVLQ1ve8sIird'
        redirect_uri = 'https://ceralfa.odoo.com/meli_login/cere'

        try:
            # Hacer la petición POST para obtener el access_token
            response = requests.post(
                'https://api.mercadolibre.com/oauth/token',
                data={
                    'grant_type': 'authorization_code',
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'code': code,
                    'redirect_uri': redirect_uri,
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            result = response.json()

            if response.status_code == 200:
                access_token = result.get('access_token')
                _logger.info(f"Token de acceso obtenido: {access_token}")
                return f"Autenticación exitosa. Token: {access_token}"
            else:
                _logger.error(f"Error en autenticación: {result}")
                return f"Error al obtener el token: {result}"

        except Exception as e:
            _logger.exception("Excepción al obtener el token de acceso")
            return f"Excepción: {str(e)}"
        
    @http.route('/meli_login/primor', type='http', auth='public', website=True)
    def meli_login_primor_callback(self, **kwargs):
        code = kwargs.get('code')
        if not code:
            return "No se recibió el código de autorización"

        _logger.info(f"Recibido código de autorización: {code}")

        # Aquí podrías buscar el client_id y client_secret desde la config o db
        client_id = '4917263316329378'
        client_secret = '2RX1zFOD5Y1QyHEE4QtrumvxsYFY5hKk'
        redirect_uri = 'https://ceralfa.odoo.com/meli_login/primor'

        try:
            # Hacer la petición POST para obtener el access_token
            response = requests.post(
                'https://api.mercadolibre.com/oauth/token',
                data={
                    'grant_type': 'authorization_code',
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'code': code,
                    'redirect_uri': redirect_uri,
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            result = response.json()

            if response.status_code == 200:
                access_token = result.get('access_token')
                _logger.info(f"Token de acceso obtenido: {access_token}")
                return f"Autenticación exitosa. Token: {access_token}"
            else:
                _logger.error(f"Error en autenticación: {result}")
                return f"Error al obtener el token: {result}"

        except Exception as e:
            _logger.exception("Excepción al obtener el token de acceso")
            return f"Excepción: {str(e)}"

    @http.route('/meli/notificationer', type='json', auth='public', methods=['POST'], csrf=False)
    def webhook_meli_order(self, **post):
        """Webhook receptor de notificaciones de Mercado Libre con manejo de errores y retry automático."""
        log_prefix = "\n========== [WEBHOOK MELI] ==========\n"

        try:
            data = request.get_json_data()
            _logger.info(f"{log_prefix}📩 Notificación recibida:\n{json.dumps(data, indent=2, ensure_ascii=False)}")

            # Validar datos mínimos
            if not all(data.get(k) for k in ('resource', 'user_id', 'topic')):
                _logger.warning(f"{log_prefix}⚠ Payload incompleto: {data}")
                return {"status": "invalid", "message": "Datos incompletos"}

            resource = data['resource']
            event_type = data['topic']
            user_id = data['user_id']
            meli_id = resource.split('/')[-1]

            # Buscar instancia asociada
            Instance = request.env['vex.instance'].sudo()
            instance = Instance.sudo().search([('meli_user_id', '=', str(user_id))], limit=1)
            if not instance:
                _logger.error(f"{log_prefix}❌ No se encontró instancia con user_id: {user_id}")
                return {"status": "error", "message": "Instancia no encontrada"}

            Queue = request.env['vex.webhook.queue'].sudo()

            # Verificar duplicados
            if Queue.sudo().search([
                ('meli_id', '=', meli_id),
                ('event_type', '=', event_type),
                ('instance_id', '=', instance.id)
            ], limit=1):
                _logger.info(f"{log_prefix}🔁 Evento ya en cola: {meli_id} - {event_type}")
                return {"status": "exists"}

            # Mapear eventos a sus handlers
            handlers = {
                # 'price_suggestion': self._handle_items_prices,
                # 'items': self._handle_items,
                'questions': self._handle_questions,
                # 'shipments': self._handle_shipments,
                'orders_v2': self._handle_orders
            }

            # Procesar evento o encolarlo si falla
            if event_type in handlers:
                self._process_event_with_retry(
                    handlers[event_type],
                    instance, resource, data, Queue, meli_id, event_type
                )
            else:
                self._enqueue_event(Queue, meli_id, event_type, instance, data)

            _logger.info(f"{log_prefix}✅ Evento {meli_id} ({event_type}) procesado o encolado correctamente.\n")
            return {"status": "success", "message": "Evento procesado"}

        except Exception as e:
            _logger.exception(f"{log_prefix}💥 Error procesando notificación: {e}")
            return {"status": "error", "message": str(e)}
        
    def _handle_items_prices(self, instance, resource, data):
        meli_item_id = resource.split('/')[-2]
        product = request.env['product.template'].sudo().search([('meli_product_id', '=', meli_item_id)], limit=1)
        if product:
            _logger.info(f"🔄 Actualizando precios para producto {meli_item_id}")
            product.action_get_details()
            product.action_get_price()

    def _handle_items(self, instance, resource, data):
        meli_item_id = resource.split('/')[-1]
        product = request.env['product.template'].sudo().search([('meli_product_id', '=', meli_item_id)], limit=1)
        if product:
            current_qty = product.meli_available_quantity
            _logger.info(f"🔄 Actualizando detalles para producto {meli_item_id}")
            product.action_get_details()
            product.action_get_price()
            if current_qty != product.meli_available_quantity:
                _logger.info(f"📦 Stock cambiado, actualizando inventario para {meli_item_id}")
                product.action_download_stock()
        else:
            product = request.env['product.template'].sudo().create({
                'meli_product_id': meli_item_id,
                'instance_id': instance.id,
                'name': f'Producto ML {meli_item_id}',
                'type': 'product',
                'sale_ok': True,
                'purchase_ok': True,
                'company_id':instance.company_id.id if instance.company_id else False
            })
            product.action_get_details()
            product.action_get_price() 

    def _handle_questions(self, instance, resource, data):
        access_token = instance.meli_access_token
        headers = {'Authorization': f'Bearer {access_token}'}
        meli_question_id = resource.split('/')[-1]
        url = f"https://api.mercadolibre.com/questions/{meli_question_id}"
        response = requests.get(url, headers=headers)
        question_data = response.json()
        meli_item_id = question_data.get('item_id')
        product = request.env['product.template'].sudo().search([('meli_product_id', '=', meli_item_id)])
        if product:
            _logger.info(f"💬 Sincronizando preguntas para producto {meli_item_id}")
            product.action_sync_questions()

    def _handle_shipments(self, instance, resource, data):
        meli_shipment_id = resource.split('/')[-1]
        sales = request.env['sale.order'].sudo().search([('meli_shipping_id', '=', meli_shipment_id)])
        for sale in sales:
            _logger.info(f"🚚 Actualizando datos de envío para pedido {sale.name}")
            sale.action_get_shipping_details()

    def _handle_orders(self, instance, resource, data):
        """
        Refactorizado: Maneja notificaciones de órdenes consultando primero la API de ML
        para evitar la creación de duplicados, especialmente en casos de packs.
        """
        log_prefix = "[WEBHOOK MELI - ORDERS]"
        meli_id_notificacion = resource.split('/')[-1]
        SaleOrder = request.env['sale.order'].sudo()

        try:
            order_data = instance.get_order(meli_id_notificacion)
            _logger.info(f"{log_prefix} Datos obtenidos de la API de ML para la orden {meli_id_notificacion}.")
        except Exception as e:
            _logger.error(f"{log_prefix} ❌ No se pudo consultar la orden {meli_id_notificacion} en la API de ML. Error: {e}")
            return

        pack_id = order_data.get('pack_id')
        id_a_procesar = str(pack_id) if pack_id else meli_id_notificacion

        if pack_id and SaleOrder.search_count([('meli_pack_id', '=', id_a_procesar)]) > 0:
            _logger.info(f"{log_prefix} ✅ El pack {id_a_procesar} ya existe en Odoo. Se omite la creación.")
            return

        domain = [
            ('state', '!=', 'cancel'),
            '|', ('meli_pack_id', '=', id_a_procesar),
            '|', ('meli_order_id', '=', id_a_procesar),
                 ('meli_sale_id', '=', id_a_procesar)
        ]
        order = SaleOrder.search(domain, limit=1)

        if not order:
            try:
                order = SaleOrder.create({
                    'meli_order_id': id_a_procesar,
                    'meli_sale_id': id_a_procesar,
                    'meli_pack_id': id_a_procesar,
                    'instance_id': instance.id,
                    'partner_id': request.env.ref('odoo-mercadolibre.res_partner_cliente_meli').id,
                    'marketplace_ids': [(4, request.env.ref('odoo-mercadolibre.vex_marketplace_mercadolibre').id)],
                    'company_id': instance.company_id.id
                })
                request.env.cr.commit()
                _logger.info(f"{log_prefix} 📦 Pedido {id_a_procesar} creado en Odoo como '{order.name}'.")
            except Exception:
                request.env.cr.rollback()
                order = SaleOrder.search(domain, limit=1)
                if not order:
                    _logger.error(f"{log_prefix} ❌ CRÍTICO: No se pudo crear ni encontrar la orden {id_a_procesar}.")
                    return

        _logger.info(f"{log_prefix} 🔄 Ejecutando acciones para la orden '{order.name}'.")
        try:
            order.action_get_details()
            order.action_get_shipping_details()
            order.action_copy_datetime_to_date()
            request.env.cr.commit()
        except Exception as e:
            _logger.exception(f"{log_prefix} 💥 Error al ejecutar acciones en la orden {order.name}: {e}")
            request.env.cr.rollback()
        
        