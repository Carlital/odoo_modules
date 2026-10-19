# -*- coding: utf-8 -*-
import logging

from werkzeug.utils import redirect
from odoo.exceptions import UserError
from odoo import _, http
from datetime import datetime, timedelta

import requests
import json
import re

from odoo.http import request

_logger = logging.getLogger(__name__)

class MeliController(http.Controller):
    
    def _log(self, message, level='info'):
        if True:
            if isinstance(message, list):
                message = ' - '.join(message)
            log_method = getattr(_logger, level, _logger.info)
            log_method(message)
            try:
                print(message)
            except UnicodeEncodeError:
                print(message.encode('utf-8', errors='replace').decode('utf-8'))
        
    @http.route('/meli/code', type='http', auth='public', website=True, csrf=False)
    def meli_redirect(self, **params):
        # Obtener todos los elementos de la sesión
        session_data = dict(request.session.items())

        # Convertir los elementos de la sesión a un formato legible
        session_data_str = "\n".join([f"{key}: {value}" for key, value in session_data.items()])

        # Registrar la sesión completa
        self._log(["Session Data:", session_data_str], level='info')
        
        # Intentar obtener el instance_id de la sesión
        session_instance_id = request.session.get('instance_id')
        server_code = params.get('code')
        self._log([f"Instance ID found in session: {session_instance_id}", f"Server code: {server_code}"], level='info')
        
        if not session_instance_id:
            self._log("Instance ID not found in session", level='error')
            return "Instance ID not found in session"

        instance = request.env['vex.instance'].sudo().browse(int(session_instance_id))
        
        if not server_code:
            self._log("Authorization code not provided", level='error')
            return "Authorization code not provided"
        
        instance.meli_server_code = server_code
        
        try:
            instance.get_access_token()
            instance.status_auth = "authenticated"
            
            try:
                instance.get_perfil()
            except UserError as e:
                instance._log(f"Failed to get profile: {str(e)}", level='error')
                return str(e)
            
            # Crear o actualizar un cron job para refrescar el token cada 5 horas
            cron_model = request.env['ir.cron'].sudo()
            model_id = request.env['ir.model'].sudo().search([('model', '=', 'vex.instance')], limit=1).id
            
            # Verificar si el cron job ya existe
            existing_cron = cron_model.search([
                ('model_id', '=', model_id),
                ('code', '=', 'model.refresh_token_all()')
            ], limit=1)
            
            if not existing_cron:
                cron_model.create({
                    'user_id': request.env.ref('base.user_root').id,  
                    'name': f"Refresh Token All Mercado Libre",
                    'model_id': model_id,
                    'state': 'code',
                    'code': 'model.refresh_token_all()',
                    'interval_number': 5,
                    'interval_type': 'hours',
                    'numbercall': -1,
                    'active': True,
                    'priority': 10,
                    # 'nextcall': (datetime.now() + timedelta(hours=5)).strftime('%Y-%m-%d %H:%M:%S')  # Forzar la siguiente ejecución
                })
                instance._log("Cron job created successfully.", level='info')
            else:
                instance._log("The cron job already exists", level='info')

        except UserError as e:
            instance._log(f"Failed to get access token: {str(e)}", level='error')
            instance.status_auth = "unauthenticated"
            return str(e)
        
        form_view_url = f"/web#id={instance.id}&view_type=form&model=vex.instance"
        
        return redirect(form_view_url)
    
    def define_topic(self, topic:str):
        intems_topics = ['items', 'items_prices']
        orders_topics = ['orders', 'orders_v2', 'orders_deleted']
        stocks_topics = ['user-products', 'stock-locations']
        questions_topics = ['questions']
        #questions_topics = tip sg_code
        if topic in intems_topics:
            return 'items'
        if topic in orders_topics:
            return 'orders'
        if topic in stocks_topics:
            return 'stocks'
        if topic in questions_topics:
            return 'questions'
        return None
    
    
    
    def handle_items(self,body, instance):
        item_id_regex = r"/items/(\w+)"
        resource = body.get('resource')
        sku = re.search(item_id_regex, resource).group(1)
        
        instance.update_item_by_sku(sku)
    
    def handle_orders(self,body, instance):
        orders_id_regex = r"/orders/(\w+)"
        resource = body.get('resource')
        order_id = re.search(orders_id_regex, resource).group(1)
        order = instance.get_order_by_id(order_id)
        # Here does't exist delete order, because the order is not deleted, only is canceled
        if request.env['sale.order'].sudo().search([('meli_order_id', '=', order_id)]):
            instance._log(f"Order {order_id} already exists",'info')
            instance.update_order(order)
        else:
            instance._log(f"Creating order {order_id}", 'info')
            instance.create_order(order)
    
    def handle_questions(self, body: dict, instance):
        questions_id_regex = r"/questions/(\w+)"
        resource = body.get('resource')
        question_id = re.search(questions_id_regex, resource).group(1)
        if request.env['vex.meli.questions'].sudo().search([('meli_id', '=', question_id)]):
            self._log(f"Question {question_id} already exists")
            instance.update_question(question_id)
        else:
            self._log(f"Creating question {question_id}")
            instance.create_question(question_id)

    
    @http.route('/meli/notification', type='http', auth='public', website=True, csrf=False)
    def meli_webhook(self, **params):
        body = request.get_json_data()
        instance = request.env['vex.instance'].sudo().search([('meli_app_id', '=', body.get('application_id')),('status_auth','=','authenticated')])
        if not instance:            
            self._log("Instance not found", "warning")
            return 'OK, Instance not found'
        
        notification_data = {
            'notification_id': body.get('_id'),
            'topic': body.get('topic'),
            'resource': body.get('resource'),
            'user_id': body.get('user_id'),
            'application_id': body.get('application_id'),
            'sent_date': self.parse_iso_datetime(body.get('sent')),
            'received_date': self.parse_iso_datetime(body.get('received')),
            'attempts': body.get('attempts'),
            'actions': ','.join(body.get('actions', [])),
            'raw_data': json.dumps(body),  # Guardar el JSON completo en un campo de texto
            'instance_id': instance.id  # Relacionar con la instancia
        }
        request.env['vex.notification'].sudo().create(notification_data)
        
        instance._log('--------------------------------------')
        instance._log("Webhook received")
        instance._log(f"App ID {body.get('application_id')}")
        instance._log(f"WEBHOOK CAPTURE: {body}", 'info')        

        admin_user_id = request.env.ref('base.user_admin').id
        # Cambia temporalmente el entorno al usuario administrador
        request.env = request.env(user=admin_user_id)
        
        self.define_topic_v2(instance, body)
        
        instance._log(f"User ID: {request.env.user.id}", 'info')        
        # try: 
        #     if topic_to_update == 'items':
        #         instance._log('In items')
        #         self.handle_items(body, instance)
        #     elif topic_to_update == 'orders':
        #         instance._log('In orders')
        #         self.handle_orders(body, instance)
        #     elif topic_to_update == 'stocks':
        #         instance._log('In stocks')
        #         stocks_id_regex = r"/user-products/(\w+)"
        #         resource = body.get('resource')
        #         product_id = re.search(stocks_id_regex, resource).group(1)
        #         instance.update_stocks_by_skus([product_id])
        #     elif topic_to_update == 'questions':
        #         instance._log("In questions")
        #         self.handle_questions(body,instance)
        #         return 'OK, Checkpoint para mi'
            
        # except UserError as e:
        #     self._log(f"Failed to get {topic_to_update}: {str(e)}", level='error')

        return 'OK'
    
    def parse_iso_datetime(self, iso_string):
        """Convierte el formato ISO 8601 a un formato compatible con Odoo."""
        try:
            return datetime.strptime(iso_string, '%Y-%m-%dT%H:%M:%S.%fZ')
        except ValueError:
            # Si la microsegundos están ausentes en la cadena
            return datetime.strptime(iso_string, '%Y-%m-%dT%H:%M:%SZ')
    
    # WEBHOOK MEJORADO
    def define_topic_v2(self,instance, response):
        known_topics = {
            'items_prices': self.process_items_prices,
            'items': self.process_items,
            'orders': self.process_orders,
            'orders_v2': self.process_orders_v2,
            'orders_deleted': self.process_orders_deleted,
            'user-products': self.process_user_products,
            'user-products-families': self.process_products_families,
            'stock-locations': self.process_stock_locations,
            'questions': self.process_questions
        }
        topic = response["topic"]
        if topic in known_topics:
            known_topics[topic](instance, response)
        else:
            instance._log(f"Unknown topic: {topic}", 'warning')

        return 'OK'
        
    def make_request(self, instance, resource):
        """Realiza una solicitud GET a la API de Mercado Libre usando el resource"""
        API_URL = f"https://api.mercadolibre.com{resource}"
        
        headers = {
            'Authorization': f"Bearer {instance.meli_access_token}"
        }
        instance._log(f"Making request to: {API_URL} , {headers}", 'info')
        
        try:
            response = requests.get(API_URL,headers=headers)
            response.raise_for_status()  # Verifica si hubo algún error
            instance._log(f"Request successful: {API_URL}", 'info')
            return response.json()  # Devolver el contenido como JSON
        except requests.exceptions.HTTPError as http_err:
            instance._log(f"HTTP error occurred: {http_err}", 'error')
        except Exception as err:
            instance._log(f"Other error occurred: {err}", 'error')

        return None

    # Procesamiento de cada topic con solicitud al resource
    def process_items_prices(self, instance, body):
        """Procesa la solicitud de 'items_prices'."""
        instance._log(f"Processing items_prices: {body['resource']}")
        response = self.make_request(instance, body['resource'])
        if response:
            # Procesar la respuesta obtenida de la API de Mercado Libre
            instance._log(f"Response data: {response}")

            product_id = response.get('id')
            instance.update_item_by_sku(product_id) # FALTA OPTIMIZAR ONE REQUEST

            prices = response.get('prices', [])

            # Iterar sobre las diferentes entradas de precios
            for price_data in prices:
                price_amount = price_data.get('amount')
                price_type = price_data.get('type')
                currency_id = price_data.get('currency_id')

                # Registrar el cambio de precio si es necesario
                # product = self.env['product.template'].sudo().search([('default_code', '=', product_id)], limit=1)
                # if product:
                #     pass
                    # product.update_price(price_amount) PRONTO

    def process_items(self, instance, body):
        """Procesa la solicitud de 'items'."""
        instance._log(f"Processing items: {body['resource']}")
        response = self.make_request(instance, body['resource'])
        if response:
            # Aquí procesas la respuesta obtenida de la API de Mercado Libre
            instance._log(f"Response data: {response}")
            product_id = response.get('id')
            instance.update_item_by_sku(product_id) # FALTA OPTIMIZAR ONE REQUEST

    def process_orders(self, instance, body):
        """Procesa la solicitud de 'orders'."""
        instance._log(f"Processing orders: {body['resource']}")
        response = self.make_request(instance, body['resource'])
        if response:
            # Aquí procesas la respuesta obtenida de la API de Mercado Libre
            instance._log(f"Response data: {response}")

    def process_orders_v2(self, instance, body):
        """Procesa la solicitud de 'orders_v2'."""
        instance._log(f"Processing orders_v2: {body['resource']}")
        response = self.make_request(instance, body['resource'])
        if response:
            # Aquí procesas la respuesta obtenida de la API de Mercado Libre
            instance._log(f"Response data: {response}")

    def process_orders_deleted(self, instance, body):
        """Procesa la solicitud de 'orders_deleted'."""
        instance._log(f"Processing orders_deleted: {body['resource']}")
        response = self.make_request(instance, body['resource'])
        if response:
            # Aquí procesas la respuesta obtenida de la API de Mercado Libre
            instance._log(f"Response data: {response}")

    def process_user_products(self, instance, body):
        """Procesa la solicitud de 'user-products'."""
        instance._log(f"Processing user-products: {body['resource']}")
        response = self.make_request(instance, body['resource'])
        if response:
            # Aquí procesas la respuesta obtenida de la API de Mercado Libre
            instance._log(f"Response data: {response}")
            
    def process_products_families(self, instance, body):
        """Procesa la solicitud de 'questions'."""
        instance._log(f"Processing questions: {body['resource']}")
        response = self.make_request(instance, body['resource'])
        if response:
            # Procesar la respuesta obtenida de la API de Mercado Libre
            instance._log(f"Response data: {response}")

            user_products_ids = response.get('user_products_ids', [])
            family_id = response.get('family_id')
            site_id = response.get('site_id')
            user_id = response.get('user_id')
            
            for product_id in user_products_ids:
                instance._log(f"Processing product: {product_id}")

        else:
            # Si no hay respuesta o la respuesta es vacía
            instance._log("No data returned from the API for products families", 'warning')
            
    def process_questions(self, instance, body):
        """Procesa la solicitud de 'questions'."""
        instance._log(f"Processing questions: {body['resource']}")
        response = self.make_request(instance, body['resource'])
        if response:
            # Aquí procesas la respuesta obtenida de la API de Mercado Libre
            instance._log(f"Response data: {response}")

    def process_stock_locations(self, instance, body):
        """Procesa la solicitud de 'stock-locations'."""
        instance._log(f"Processing stock-locations: {body['resource']}")
        response = self.make_request(instance, body['resource'])
        if response:
            # Procesar la respuesta obtenida de la API de Mercado Libre
            instance._log(f"Response data: {response}")
            
            user_id = response.get('user_id')
            if user_id != instance.perfil_id:
                instance._log(f"Error: el perfil del webhook no coincide con la instancia User_id:{user_id} - Instance:{instance.perfil_id} .", 'error')
                return  # Detener el procesamiento si no coinciden
            
            user_product_id = response.get('id') 
            locations = response.get('locations', [])
            product_release_date = response.get('product_release_date', None)

            # Iterar sobre las ubicaciones y registrar la cantidad disponible
            for location in locations:
                location_type = location.get('type')
                quantity = location.get('quantity', 0)
                instance._log(f"Location Type: {location_type}, Quantity: {quantity}")
            # Hacer la solicitud paginada
            # Hacer la solicitud paginada y obtener los IDs de los items y errores
            item_ids, errors = self.get_items_by_user_product(instance, user_id, user_product_id)
            
            if item_ids:
                instance._log(f"Successfully retrieved item IDs: {item_ids}")
                # Iterar sobre cada item_id y ejecutar una función para procesar cada uno
                for item_id in item_ids:
                    instance.update_item_by_sku(item_id)  # Ejecutar la función para cada item
                    
            if errors:
                instance._log(f"Errors occurred while fetching items: {errors}")

        else:
            # Si no hay respuesta o la respuesta es vacía
            instance._log("No data returned from the API for stock-locations", 'warning')
            
    # UTILS
    def get_items_by_user_product(self, instance, user_id, user_product_id):
        """Realiza una solicitud paginada a la API de Mercado Libre para obtener los items de un usuario basado en user_product_id."""
        
        # Inicialización de variables para paginación
        url = f"https://api.mercadolibre.com/users/{user_id}/items/search?user_product_id={user_product_id}"
        headers = {
            'Authorization': f'Bearer {instance.meli_access_token}'
        }
        limit = 50  # Límite de resultados por página
        offset = 0  # Comienza en la primera página
        total = 1  # Número inicial de elementos, se actualizará con la primera respuesta
        
        all_item_ids = []  # Lista para almacenar todos los IDs de los items
        errors = []  # Lista para almacenar los errores ocurridos durante la paginación
        
        while offset < total:
            # Actualizar la URL con el límite y el offset
            paginated_url = f"{url}&limit={limit}&offset={offset}"
            instance._log(f"Making paginated request to: {paginated_url}", 'info')
            
            try:
                response = requests.get(paginated_url, headers=headers)
                response.raise_for_status()  # Verifica si hubo algún error
                data = response.json()  # Obtener los datos en formato JSON
                
                # Agregar los resultados (IDs de los items) a la lista all_item_ids
                item_ids = data.get('results', [])
                all_item_ids.extend(item_ids)

                # Actualizar la paginación
                total = data.get('paging', {}).get('total', 1)  # Total de resultados
                offset += limit  # Aumentar el offset para la siguiente página

                instance._log(f"Processed page with offset {offset}, total results {total}", 'info')
            
            except requests.exceptions.HTTPError as http_err:
                error_message = f"HTTP error occurred for offset {offset}: {http_err}"
                instance._log(error_message, 'error')
                errors.append(error_message)
                break
            except Exception as err:
                error_message = f"Other error occurred for offset {offset}: {err}"
                instance._log(error_message, 'error')
                errors.append(error_message)
                break
        
        return all_item_ids, errors

        
        
        
