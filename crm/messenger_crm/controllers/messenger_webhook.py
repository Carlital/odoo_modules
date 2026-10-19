import logging
import json
import time
import requests
from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

class MessengerWebhook(http.Controller):
    VERIFY_TOKEN = 'my_verification_token'
    ACCESS_TOKEN = 'EAAOZBIJfmb00BO8IBEvCrJq0NgUVA59PaDvHjZCwjdi6rUmkWq8IflUe3I2GmSc5NLZBG1lfHWsQP0yZCpUi2ZCajrEuvDK7PTX6y6WlDI8tZBAMKkDHH8OGx5tAdCuUvs0kZAFmY8garVVzckRBKiKUiZCeZAGrSacaKGe8b7rOmsiUgsfDTuj6bdypVcINXehObwve2DRZCrU0pFXdskaQZDZD'

    user_selection = {}

    @http.route('/messenger/webhook', type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def messenger_webhook(self, **kwargs):
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

                        # Obtener perfil del usuario
                        self.get_user_profile(sender_id)
                        
                        if 'quick_reply' in messaging_event.get('message', {}):
                            quick_reply = messaging_event['message']['quick_reply']['payload']
                            _logger.info("Quick reply received: %s", quick_reply)
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
                                # Handle product category selection
                                self.send_product_options(sender_id, quick_reply)
                        else:
                            text = messaging_event.get('message', {}).get('text')
                            _logger.info("Text message received: %s", text)
                            if text:
                                if text.lower() in ['hola', 'menu']:
                                    self.send_main_menu(sender_id)
                                else:
                                    ai_model = request.env['crm.ai'].sudo()
                                    ai_response = ai_model.get_ai_response(text)
                                    self.send_text_message(sender_id, ai_response)

                return Response(json.dumps({'status': 'success'}), content_type='application/json', status=200)
            except Exception as e:
                _logger.error("Error processing webhook: %s", str(e))
                _logger.error("Request data: %s", request.httprequest.data)
                return Response(json.dumps({'error': str(e)}), content_type='application/json', status=500)

    def get_user_profile(self, sender_id):
        url = f"https://graph.facebook.com/{sender_id}"
        params = {
            "fields": "email,name",
            "access_token": self.ACCESS_TOKEN
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            profile = response.json()
            email = profile.get("email")
            name = profile.get("name")
            if email:
                _logger.info("Email retrieved for %s: %s", sender_id, email)
                self.user_selection[sender_id]['email'] = email
            else:
                _logger.warning("No email found for user %s", sender_id)
            if name:
                _logger.info("Name retrieved for %s: %s", sender_id, name)
                self.user_selection[sender_id]['name'] = name
            else:
                _logger.warning("No name found for user %s", sender_id)
        else:
            _logger.error("Failed to retrieve profile for %s: %s", sender_id, response.text)

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
        self.send_messenger_message(sender_id, payload)

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
            self.send_messenger_message(sender_id, payload)
        else:
            _logger.info("No products available in category: %s", category_name)
            self.send_text_message(sender_id, f"🚫 Lo sentimos, pero actualmente no hay productos disponibles en la categoría {category_name}.")

    def handle_product_selection(self, sender_id, quick_reply):
        try:
            product_id = int(quick_reply.split('_')[1])
            _logger.info("Handling product selection for %s with product ID: %d", sender_id, product_id)
            product = request.env['product.product'].sudo().search([('id', '=', product_id)], limit=1)
            if product:
                _logger.info("Product details: %s", product.read(['id', 'name', 'default_code', 'pdf_url', 'color_1', 'color_2', 'color_3']))
                if sender_id not in self.user_selection:
                    self.user_selection[sender_id] = {}
                self.user_selection[sender_id]['product_id'] = product.id
                self.send_product_details(sender_id, product)
            else:
                _logger.info("Product not found with ID: %d", product_id)
                self.send_text_message(sender_id, "Producto no encontrado. Por favor, intenta nuevamente.")
        except Exception as e:
            _logger.error("Error handling product selection: %s", str(e))
            self.send_text_message(sender_id, "Ocurrió un error al procesar tu solicitud. Por favor, intenta nuevamente.")

    def send_product_details(self, sender_id, product):
        _logger.info("Sending product details to %s for product: %s", sender_id, product.name)
        message = (
            f"📦 *Detalles del producto seleccionado:*\n"
        )
        self.send_text_message(sender_id, message)
        
        if product.pdf_data:
            pdf_url = self.get_drive_download_link(product.pdf_url)
            _logger.info("Sending PDF message to %s with URL: %s", sender_id, pdf_url)
            pdf_sent = self.send_pdf_message(sender_id, pdf_url)
            if pdf_sent:
                _logger.info("PDF sent successfully, now waiting before asking for color.")
                time.sleep(3)
                self.ask_for_color(sender_id, product)
            else:
                _logger.error("Failed to send PDF, not asking for color.")
        else:
            _logger.error("No PDF data found for product, not sending PDF.")
            self.ask_for_color(sender_id, product)

    def get_drive_download_link(self, url):
        _logger.info("Generating Google Drive download link from URL: %s", url)
        if "drive.google.com" in url:
            file_id = url.split("/d/")[1].split("/")[0]
            return f"https://drive.google.com/uc?export=download&id={file_id}"
        return url

    def send_pdf_message(self, sender_id, pdf_url):
        payload = {
            "recipient": {
                "id": sender_id
            },
            "message": {
                "attachment": {
                    "type": "file",
                    "payload": {
                        "url": pdf_url
                    }
                }
            }
        }
        try:
            _logger.info("Sending Messenger PDF message to %s with payload: %s", sender_id, json.dumps(payload))
            url = f"https://graph.facebook.com/v21.0/me/messages?access_token={self.ACCESS_TOKEN}"
            headers = {
                "Content-Type": "application/json"
            }
            response = requests.post(url, headers=headers, json=payload)
            _logger.info("Messenger API response for PDF: %s - %s", response.status_code, response.text)
            return response.status_code == 200
        except Exception as e:
            _logger.error("Error sending Messenger PDF message: %s", str(e))
            return False

    def ask_for_color(self, sender_id, product):
        _logger.info("Asking for color selection for product: %s", product.name)
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
        self.send_messenger_message(sender_id, payload)

    def handle_color_selection(self, sender_id, quick_reply):
        try:
            product_id, color = quick_reply.split('_', 2)[1:]
            product_id = int(product_id)
            _logger.info("Handling color selection for product ID: %d with color: %s", product_id, color)
            product = request.env['product.product'].sudo().search([('id', '=', product_id)], limit=1)
            if product:
                price = None
                if color == product.color_1:
                    price = product.color_1_price
                elif color == product.color_2:
                    price = product.color_2_price
                elif color == product.color_3:
                    price = product.color_3_price

                if price is not None:
                    _logger.info("Color selected: %s with price: %s", color, price)
                    self.user_selection[sender_id]['color'] = color
                    self.user_selection[sender_id]['price'] = price
                    self.user_selection[sender_id]['promotion'] = product.promotion
                    message = (
                        f"🔹 *Precio:* ${price}\n"
                    )
                    if product.promotion:
                        message += f"🎉 *Promoción:* {product.promotion}\n"
                    
                    self.send_text_message(sender_id, message)
                    
                    self.ask_for_payment_options(sender_id, product, price)
                else:
                    _logger.error("Price for color %s not found", color)
                    self.send_text_message(sender_id, "Ocurrió un error al obtener el precio del color seleccionado.")
            else:
                _logger.error("Product not found with ID: %d", product_id)
                self.send_text_message(sender_id, "Producto no encontrado. Por favor, intenta nuevamente.")
        except Exception as e:
            _logger.error("Error handling color selection: %s", str(e))
            self.send_text_message(sender_id, "Ocurrió un error al procesar tu solicitud. Por favor, intenta nuevamente.")

    def ask_for_payment_options(self, sender_id, product, price):
        _logger.info("Asking for payment options for product: %s with price: %s", product.name, price)
        quick_replies = [
            {
                "content_type": "text",
                "title": "24 meses",
                "payload": f"payment_{product.id}_24_{price}"
            },
            {
                "content_type": "text",
                "title": "36 meses",
                "payload": f"payment_{product.id}_36_{price}"
            },
            {
                "content_type": "text",
                "title": "48 meses",
                "payload": f"payment_{product.id}_48_{price}"
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
        self.send_messenger_message(sender_id, payload)

    def handle_payment_option(self, sender_id, quick_reply):
        try:
            parts = quick_reply.split('_')
            product_id = int(parts[1])
            months = int(parts[2])
            price = float(parts[3])

            monthly_payment = price / months

            _logger.info("Handling payment option for product ID: %d with months: %d and monthly payment: %.2f", product_id, months, monthly_payment)

            self.user_selection[sender_id]['payment_option'] = f"{months} meses"
            self.user_selection[sender_id]['monthly_payment'] = monthly_payment

            message = (
                f"💳 *Opción de pago seleccionada: {months} meses*\n"
                f"🔹 *Cuota mensual:* ${monthly_payment:.2f}\n\n"
                "¿Te gustaría hacer un Test Drive o ser contactado por un asesor?\n"
            )
            quick_replies = [
                {
                    "content_type": "text",
                    "title": "Test Drive",
                    "payload": f"action_{product_id}_test_drive"
                },
                {
                    "content_type": "text",
                    "title": "Ser Contactado",
                    "payload": f"action_{product_id}_contact"
                }
            ]
            payload = {
                "recipient": {
                    "id": sender_id
                },
                "message": {
                    "text": message,
                    "quick_replies": quick_replies
                }
            }
            self.send_messenger_message(sender_id, payload)
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
                message = (
                    f"Acción seleccionada: {action.replace('_', ' ').capitalize()}\n"
                    "¡Gracias! Un asesor se pondrá en contacto contigo pronto."
                )
                self.send_text_message(sender_id, message)
        except Exception as e:
            _logger.error("Error handling action option: %s", str(e))
            self.send_text_message(sender_id, "Ocurrió un error al procesar tu solicitud. Por favor, intenta nuevamente.")

    def ask_for_test_drive_date(self, sender_id):
        _logger.info("Asking for test drive date for sender ID: %s", sender_id)
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
        self.send_messenger_message(sender_id, payload)

    def handle_test_drive_date_selection(self, sender_id, quick_reply):
        try:
            selected_date = quick_reply.split('_')[3]
            _logger.info("Test drive date selected: %s for sender ID: %s", selected_date, sender_id)
            self.user_selection[sender_id]['test_drive_date'] = selected_date
            times = self.get_available_test_drive_times(selected_date)
            unique_times = list(set(times))
            unique_times.sort()
            quick_replies = [
                {
                    "content_type": "text",
                    "title": f"{int(time)}:00",
                    "payload": f"test_drive_time_{selected_date}_{time}"
                }
                for time in unique_times
            ]

            payload = {
                "recipient": {
                    "id": sender_id
                },
                "message": {
                    "text": "🚗 *Por favor, selecciona una hora para tu Test Drive.*",
                    "quick_replies": quick_replies
                }
            }
            self.send_messenger_message(sender_id, payload)
        except Exception as e:
            _logger.error("Error handling test drive date selection: %s", str(e))
            self.send_text_message(sender_id, "Ocurrió un error al procesar tu solicitud. Por favor, intenta nuevamente.")

    def handle_test_drive_time_selection(self, sender_id, quick_reply):
        try:
            selected_date, selected_time = quick_reply.split('_')[3:5]
            _logger.info("Test drive time selected: %s on date: %s for sender ID: %s", selected_time, selected_date, sender_id)
            self.user_selection[sender_id]['test_drive_time'] = selected_time
            self.reserve_test_drive_slot(selected_date, selected_time)
            self.create_lead(sender_id, test_drive=True)
            message = (
                "🚗 *Test Drive programado*\n"
                f"Fecha: {selected_date}\n"
                f"Hora: {selected_time}\n\n"
                "¡Gracias! Te esperamos para tu Test Drive."
            )
            self.send_text_message(sender_id, message)
        except Exception as e:
            _logger.error("Error handling test drive time selection: %s", str(e))
            self.send_text_message(sender_id, "Ocurrió un error al procesar tu solicitud. Por favor, intenta nuevamente.")

    def get_available_test_drive_dates(self):
        _logger.info("Retrieving available test drive dates")
        slots = request.env['test.drive.configuration'].sudo().search([('available', '=', True)])
        dates = list(set(slot.date for slot in slots))
        _logger.info("Available test drive dates: %s", dates)
        return sorted(dates)

    def get_available_test_drive_times(self, date):
        _logger.info("Retrieving available test drive times for date: %s", date)
        slots = request.env['test.drive.configuration'].sudo().search([('date', '=', date), ('available', '=', True)])
        times = [slot.time for slot in slots]
        _logger.info("Available test drive times for date %s: %s", date, times)
        return sorted(times)

    def reserve_test_drive_slot(self, date, time):
        _logger.info("Reserving test drive slot for date: %s and time: %s", date, time)
        slot = request.env['test.drive.configuration'].sudo().search([('date', '=', date), ('time', '=', time)], limit=1)
        if slot:
            slot.write({'available': False})
            _logger.info("Test drive slot reserved for date: %s and time: %s", date, time)
        else:
            _logger.warning("No available test drive slot found for date: %s and time: %s", date, time)

    def create_lead(self, sender_id, test_drive=False):
        _logger.info("Creating lead for sender ID: %s", sender_id)
        user_selection = self.user_selection.get(sender_id, {})
        product_id = user_selection.get('product_id')
        color = user_selection.get('color')
        price = user_selection.get('price')
        promotion = user_selection.get('promotion')
        payment_option = user_selection.get('payment_option')
        monthly_payment = user_selection.get('monthly_payment')
        test_drive_date = user_selection.get('test_drive_date') if test_drive else None
        test_drive_time = user_selection.get('test_drive_time') if test_drive else None
        test_drive = True if test_drive_date and test_drive_time else False
        email = user_selection.get('email')
        name = user_selection.get('name')
        _logger.info("Valor de test_drive: %s", test_drive)
        if not product_id:
            _logger.error("Product ID is not found in user_selection for sender ID: %s", sender_id)
            self.send_text_message(sender_id, "Error: No se encontró el ID del producto seleccionado.")
            return

        product = request.env['product.product'].sudo().browse(product_id)
        if not product.exists():
            _logger.error("Product with ID %s does not exist in the database", product_id)
            self.send_text_message(sender_id, "Error: El producto seleccionado no existe.")
            return

        _logger.info("Selected Product Code: %s", product.default_code)
        _logger.info("Selected Product Name: %s", product.name)
        lead_vals = {
            'name': f"Oportunidad para {user_selection.get('name', sender_id)}",
            'partner_name': name,
            'phone': sender_id,
            'email_from': email,
            'selected_product_id': product.id,
            'selected_product_code': product.default_code,
            'color': color,
            'price': price,
            'promotion': promotion,
            'payment_option': payment_option,
            'monthly_payment': monthly_payment,
            'test_drive': test_drive,
            'test_drive_date': test_drive_date,
            'test_drive_time': test_drive_time,
        }
        if test_drive:
            stage_1_id = request.env['crm.stage'].search([('name', '=', 'New')], limit=1).id
            lead_vals['stage_id'] = stage_1_id
        request.env['crm.lead'].sudo().create(lead_vals)
        _logger.info("Lead created for sender ID: %s", sender_id)

    def send_messenger_message(self, sender_id, payload):
        try:
            _logger.info("Sending Messenger message to %s with payload: %s", sender_id, json.dumps(payload))
            url = f"https://graph.facebook.com/v21.0/me/messages?access_token={self.ACCESS_TOKEN}"
            headers = {
                "Content-Type": "application/json"
            }
            response = requests.post(url, headers=headers, json=payload)
            _logger.info("Messenger API response: %s - %s", response.status_code, response.text)
        except Exception as e:
            _logger.error("Error sending Messenger message: %s", str(e))

    def send_text_message(self, sender_id, message):
        _logger.info("Sending text message to %s", sender_id)
        payload = {
            "recipient": {
                "id": sender_id
            },
            "message": {
                "text": message
            }
        }
        self.send_messenger_message(sender_id, payload)

    def get_products_by_category(self, category_name):
        _logger.info("Retrieving products for category: %s", category_name)
        products = request.env['product.product'].sudo().search([
            ('categ_id.name', '=', category_name),
            ('qty_available', '>', 0),
            ('active', '=', True)
        ])
        _logger.info("Products found: %s", products)
        return products
