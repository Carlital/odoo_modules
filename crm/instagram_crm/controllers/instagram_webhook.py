import logging
import json
import requests
from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

class InstagramWebhook(http.Controller):
    VERIFY_TOKEN = 'my_verification_token'
    ACCESS_TOKEN = 'EAAGjJPvimY4BO1aQWYGRjgqW8bSm3bLUiEVwdX7kcf1mfiXZCYdvgmIzwJdZARlDzp6lWZBuABY12oZAl5rXp31ycQFlWZA22DKM73aBcR5hVRs9dOtYRv0m8NhlDiWelOPJZAKrqzofhNBZCpQLFP1JMjbbf6FxP7yJA3ZBf86ZAk7kVgZCZAE86NCjUgqFO3RXnZAqPAZDZD'

    user_selection = {}

    @http.route('/instagram/webhook', type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def instagram_webhook(self, **kwargs):
        _logger.info("Received request with method: %s", request.httprequest.method)
        if request.httprequest.method == 'GET':
            token = kwargs.get('hub.verify_token')
            challenge = kwargs.get('hub.challenge')
            _logger.info("GET request with token: %s and challenge: %s", token, challenge)
            if token == self.VERIFY_TOKEN:
                return Response(challenge)
            else:
                return Response('Error, invalid token', status=403)
        elif request.httprequest.method == 'POST':
            try:
                _logger.info("Processing POST request")
                data = json.loads(request.httprequest.data)
                _logger.info("Incoming message data: %s", json.dumps(data, indent=2))

                if 'entry' not in data:
                    _logger.warning('No entry in data')
                    return Response(json.dumps({'status': 'no entry in data'}), content_type='application/json', status=200)

                for entry in data.get('entry', []):
                    for messaging_event in entry.get('messaging', []):
                        sender_id = messaging_event.get('sender', {}).get('id')
                        _logger.info("Processing message from %s", sender_id)
                        if sender_id not in self.user_selection:
                            self.user_selection[sender_id] = {}

                        if 'quick_reply' in messaging_event.get('message', {}):
                            quick_reply = messaging_event['message']['quick_reply']['payload']
                            _logger.info("Quick reply received: %s", quick_reply)
                            self.handle_quick_reply(sender_id, quick_reply)
                        else:
                            text = messaging_event.get('message', {}).get('text')
                            _logger.info("Text message received: %s", text)
                            if text:
                                self.handle_text_message(sender_id, text)

                return Response(json.dumps({'status': 'success'}), content_type='application/json', status=200)
            except Exception as e:
                _logger.error("Error processing webhook: %s", str(e))
                _logger.error("Request data: %s", request.httprequest.data)
                return Response(json.dumps({'error': str(e)}), content_type='application/json', status=500)

    def handle_quick_reply(self, sender_id, quick_reply):
        try:
            if quick_reply.startswith('color_'):
                self.handle_color_selection(sender_id, quick_reply)
            elif quick_reply.startswith('payment_'):
                self.handle_payment_option(sender_id, quick_reply)
            elif quick_reply.startswith('action_'):
                self.handle_action_option(sender_id, quick_reply)
            elif quick_reply.startswith('test_drive_date_'):
                self.handle_test_drive_date_selection(sender_id, quick_reply)
            elif quick_reply.startswith('test_drive_time_'):
                self.handle_test_drive_time_selection(sender_id, quick_reply)
            elif quick_reply.startswith('product_'):
                self.handle_product_selection(sender_id, quick_reply)
            else:
                self.send_product_options(sender_id, quick_reply)
        except IndexError:
            _logger.error("Error handling quick reply: Index out of range for quick reply: %s", quick_reply)
            self.send_text_message(sender_id, "Ocurrió un error al procesar tu solicitud. Por favor, intenta nuevamente.")

    def handle_text_message(self, sender_id, text):
        if text.lower() in ['hola', 'menu']:
            self.send_main_menu(sender_id)
        else:
            self.handle_product_selection(sender_id, text)

    def send_main_menu(self, sender_id):
        _logger.info("Sending main menu to %s", sender_id)
        quick_replies = [
            {
                "content_type": "text",
                "title": "SWM",
                "payload": "SWM"
            },
            {
                "content_type": "text",
                "title": "DFSK",
                "payload": "DFSK"
            }
        ]
        payload = {
            "recipient": {
                "id": sender_id
            },
            "message": {
                "text": "👋 ¡Hola, bienvenido a nuestro servicio! \n\n💡 Para comenzar, por favor revisa nuestro catálogo de marcas. 👇",
                "quick_replies": quick_replies
            }
        }
        self.send_instagram_message(payload)

    def send_product_options(self, sender_id, category_name):
        _logger.info("Sending product options for category: %s to %s", category_name, sender_id)
        products = self.get_products_by_category(category_name)
        _logger.info("Products retrieved: %s", products)
        if products:
            quick_replies = [
                {
                    "content_type": "text",
                    "title": f"{product.name}",
                    "payload": f"product_{product.id}"
                }
                for product in products
            ]
            payload = {
                "recipient": {
                    "id": sender_id
                },
                "message": {
                    "text": f"🔍 Aquí tienes una selección de modelos disponibles en la marca {category_name}. Por favor, elige uno de la lista para más detalles 👇:",
                    "quick_replies": quick_replies
                }
            }
            self.send_instagram_message(payload)
        else:
            _logger.info("No products available in category: %s", category_name)
            self.send_text_message(sender_id, f"🚫 Lo sentimos, pero actualmente no hay productos disponibles en la categoría {category_name}.")

    def handle_product_selection(self, sender_id, quick_reply):
        try:
            if '_' in quick_reply:
                product_id = int(quick_reply.split('_')[1])
                _logger.info("Handling product selection for %s with product ID: %d", sender_id, product_id)
                product = request.env['product.product'].sudo().search([('id', '=', product_id)], limit=1)
                if product:
                    if sender_id not in self.user_selection:
                        self.user_selection[sender_id] = {}
                    self.user_selection[sender_id]['product_id'] = product.id
                    self.send_product_details(sender_id, product)
                else:
                    self.send_text_message(sender_id, "Producto no encontrado. Por favor, intenta nuevamente.")
            else:
                self.send_text_message(sender_id, "Ocurrió un error al procesar tu solicitud. Por favor, intenta nuevamente.")
        except Exception as e:
            _logger.error("Error handling product selection: %s", str(e))
            self.send_text_message(sender_id, "Ocurrió un error al procesar tu solicitud. Por favor, intenta nuevamente.")

    def send_product_details(self, sender_id, product):
        _logger.info("Sending product details to %s for product: %s", sender_id, product.name)
        message = (
            f"📦 *Detalles del producto seleccionado:*\n"
            f"Nombre: {product.name}\n"
            f"Código: {product.default_code}\n"
        )
        self.send_text_message(sender_id, message)
        self.ask_for_color(sender_id, product)

    def ask_for_color(self, sender_id, product):
        colors = [product.color_1, product.color_2, product.color_3]
        quick_replies = [
            {
                "content_type": "text",
                "title": color,
                "payload": f"color_{product.id}_{color}"
            }
            for color in colors if color
        ]

        payload = {
            "recipient": {
                "id": sender_id
            },
            "message": {
                "text": "🎨 *Por favor, indícame el color que te gustaría.*",
                "quick_replies": quick_replies
            }
        }
        self.send_instagram_message(payload)

    def handle_color_selection(self, sender_id, quick_reply):
        try:
            product_id, color = quick_reply.split('_', 2)[1:]
            product_id = int(product_id)
            _logger.info("Handling color selection for product ID: %d with color: %s", product_id, color)
            product = request.env['product.product'].sudo().search([('id', '=', product_id)], limit=1)
            if product:
                self.user_selection[sender_id]['color'] = color
                self.send_text_message(sender_id, f"Color seleccionado: {color}")
                self.ask_for_payment_options(sender_id, product)
            else:
                self.send_text_message(sender_id, "Producto no encontrado. Por favor, intenta nuevamente.")
        except Exception as e:
            _logger.error("Error handling color selection: %s", str(e))
            self.send_text_message(sender_id, "Ocurrió un error al procesar tu solicitud. Por favor, intenta nuevamente.")

    def ask_for_payment_options(self, sender_id, product):
        quick_replies = [
            {
                "content_type": "text",
                "title": "24 meses",
                "payload": f"payment_{product.id}_24"
            },
            {
                "content_type": "text",
                "title": "36 meses",
                "payload": f"payment_{product.id}_36"
            },
            {
                "content_type": "text",
                "title": "48 meses",
                "payload": f"payment_{product.id}_48"
            }
        ]

        payload = {
            "recipient": {
                "id": sender_id
            },
            "message": {
                "text": "💳 *Por favor, selecciona una opción de pago.*",
                "quick_replies": quick_replies
            }
        }
        self.send_instagram_message(payload)

    def handle_payment_option(self, sender_id, quick_reply):
        try:
            parts = quick_reply.split('_')
            product_id = int(parts[1])
            months = int(parts[2])
            _logger.info("Handling payment option for product ID: %d with months: %d", product_id, months)
            self.user_selection[sender_id]['payment_option'] = f"{months} meses"
            self.send_text_message(sender_id, f"💳 *Opción de pago seleccionada: {months} meses*")
        except Exception as e:
            _logger.error("Error handling payment option: %s", str(e))
            self.send_text_message(sender_id, "Ocurrió un error al procesar tu solicitud. Por favor, intenta nuevamente.")

    def handle_action_option(self, sender_id, quick_reply):
        try:
            product_id, action = quick_reply.split('_', 2)[1:]
            _logger.info("Handling action option for product ID: %d with action: %s", int(product_id), action)
            if action == 'test_drive':
                self.ask_for_test_drive_date(sender_id)
            elif action == 'contact':
                self.create_lead(sender_id)
                self.send_text_message(sender_id, "¡Gracias! Un asesor se pondrá en contacto contigo pronto.")
        except Exception as e:
            _logger.error("Error handling action option: %s", str(e))
            self.send_text_message(sender_id, "Ocurrió un error al procesar tu solicitud. Por favor, intenta nuevamente.")

    def ask_for_test_drive_date(self, sender_id):
        dates = self.get_available_test_drive_dates()
        quick_replies = [
            {
                "content_type": "text",
                "title": date.strftime('%Y-%m-%d'),
                "payload": f"test_drive_date_{date}"
            }
            for date in dates
        ]

        payload = {
            "recipient": {
                "id": sender_id
            },
            "message": {
                "text": "🚗 *Por favor, selecciona una fecha para tu Test Drive.*",
                "quick_replies": quick_replies
            }
        }
        self.send_instagram_message(payload)

    def handle_test_drive_date_selection(self, sender_id, quick_reply):
        try:
            selected_date = quick_reply.split('_')[3]
            _logger.info("Test drive date selected: %s for sender ID: %s", selected_date, sender_id)
            self.user_selection[sender_id]['test_drive_date'] = selected_date
            self.send_text_message(sender_id, f"🚗 *Fecha de Test Drive seleccionada: {selected_date}*")
        except Exception as e:
            _logger.error("Error handling test drive date selection: %s", str(e))
            self.send_text_message(sender_id, "Ocurrió un error al procesar tu solicitud. Por favor, intenta nuevamente.")

    def get_available_test_drive_dates(self):
        slots = request.env['test.drive.configuration'].sudo().search([('available', '=', True)])
        dates = list(set(slot.date for slot in slots))
        return sorted(dates)

    def create_lead(self, sender_id, test_drive=False):
        user_selection = self.user_selection.get(sender_id, {})
        product_id = user_selection.get('product_id')
        color = user_selection.get('color')
        payment_option = user_selection.get('payment_option')
        test_drive_date = user_selection.get('test_drive_date') if test_drive else None
        test_drive_time = user_selection.get('test_drive_time') if test_drive else None
        test_drive = True if test_drive_date and test_drive_time else False

        if not product_id:
            self.send_text_message(sender_id, "Error: No se encontró el ID del producto seleccionado.")
            return

        product = request.env['product.product'].sudo().browse(product_id)
        if not product.exists():
            self.send_text_message(sender_id, "Error: El producto seleccionado no existe.")
            return

        lead_vals = {
            'name': f"Oportunidad para {sender_id}",
            'partner_name': sender_id,
            'phone': sender_id,
            'selected_product_id': product.id,
            'selected_product_code': product.default_code,
            'color': color,
            'payment_option': payment_option,
            'test_drive': test_drive,
            'test_drive_date': test_drive_date,
            'test_drive_time': test_drive_time,
        }
        request.env['crm.lead'].sudo().create(lead_vals)

    def send_instagram_message(self, payload):
        try:
            url = f"https://graph.facebook.com/v13.0/me/messages?access_token={self.ACCESS_TOKEN}"
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, headers=headers, json=payload)
            _logger.info("Instagram API response: %s - %s", response.status_code, response.text)
        except Exception as e:
            _logger.error("Error sending Instagram message: %s", str(e))

    def send_text_message(self, sender_id, message):
        payload = {
            "recipient": {
                "id": sender_id
            },
            "message": {
                "text": message
            }
        }
        self.send_instagram_message(payload)

    def get_products_by_category(self, category_name):
        products = request.env['product.product'].sudo().search([
            ('categ_id.name', '=', category_name),
            ('qty_available', '>', 0),
            ('active', '=', True)
        ])
        return products
