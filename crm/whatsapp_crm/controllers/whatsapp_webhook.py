import logging
import json
import requests
import base64
import time
from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

class WhatsAppWebhook(http.Controller):
    VERIFY_TOKEN = 'my_verification_token'
    user_sessions = {}

    STICKERS = {
        "hola": "https://drive.google.com/uc?export=download&id=1T1ikzP0T809U5uMT6cC25csU5hJ_6oIr",
        "si": "https://drive.google.com/uc?export=download&id=1i0FWi1p616OWOa4sc0GClDL9PBWbOLQM",
        "no": "https://drive.google.com/uc?export=download&id=1kCpHJhn17aix8lNND5bbiVYbg3O0BTnh",
        "like": "https://drive.google.com/uc?export=download&id=1EM4Mh1xtrp3ZgofrQZMv3rk-Hrm8G0U-"
    }

    @http.route('/whatsapp/webhook', type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def whatsapp_webhook(self, **kwargs):
        """Maneja las solicitudes del webhook de WhatsApp."""
        access_token = request.env['ir.config_parameter'].sudo().get_param('whatsapp_access_token')

        if not access_token:
            _logger.error("No WhatsApp access token configured")
            return Response('Error, no access token configured', status=500)

        if request.httprequest.method == 'GET':
            token = kwargs.get('hub.verify_token')
            challenge = kwargs.get('hub.challenge')

            if token == self.VERIFY_TOKEN:
                return Response(challenge, status=200, content_type="text/plain")
            else:
                return Response('Error, invalid token', status=403)

        if request.httprequest.method == 'POST':
            try:
                data = json.loads(request.httprequest.data)

                for entry in data.get('entry', []):
                    for change in entry.get('changes', []):
                        value = change.get('value', {})
                        if 'messages' not in value:
                            continue

                        for message in value.get('messages', []):
                            phone_number = message.get('from')

                            # Detectar si el mensaje es interactivo (botón de selección en la lista)
                            if 'interactive' in message:
                                if 'list_reply' in message['interactive']:
                                    text = message['interactive']['list_reply']['title'].strip()
                                elif 'button_reply' in message['interactive']:
                                    text = message['interactive']['button_reply']['id']
                                else:
                                    text = ""
                            else:
                                text = message.get('text', {}).get('body', '').strip()

                            invalid_input = True
                            text_lower = text.lower()

                            if text_lower in self.STICKERS:
                                self.send_sticker(phone_number, self.STICKERS[text_lower])
                                invalid_input = False

                            if text_lower in ["hola", "menu"]:
                                self.user_sessions[phone_number] = {"step": "category"}
                                self.send_main_menu(phone_number)
                                invalid_input = False
                                continue

                            if phone_number not in self.user_sessions:
                                self.user_sessions[phone_number] = {"step": "category"}
                                self.send_main_menu(phone_number)
                                invalid_input = False
                                continue

                            step = self.user_sessions[phone_number]["step"]

                            if step == "category":
                                categories = self.get_categories()
                                if text_lower in [cat.lower() for cat in categories]:
                                    self.user_sessions[phone_number]["step"] = "subcategory"
                                    self.user_sessions[phone_number]["selected_category"] = text
                                    self.send_subcategories(phone_number, text)
                                    invalid_input = False
                                else:
                                    self.send_text_message(phone_number, "Por favor, selecciona una categoría válida.")
                                continue

                            # Manejo del paso "subcategory"
                            if step == "subcategory":
                                selected_category = self.user_sessions[phone_number]["selected_category"]
                                subcategories = self.get_subcategories_from_category(selected_category)
                                if text_lower in [sub.lower() for sub in subcategories]:
                                    self.user_sessions[phone_number]["step"] = "product"
                                    self.user_sessions[phone_number]["selected_subcategory"] = text
                                    self.send_product_menu(phone_number, text)
                                    invalid_input = False
                                else:
                                    self.send_text_message(phone_number, "Por favor, selecciona una subcategoría válida.")
                                continue

                            # Manejo del paso "product"
                            if step == "product":
                                selected_subcategory = self.user_sessions[phone_number]["selected_subcategory"]
                                products = self.get_products_from_subcategory(selected_subcategory)
                                if text_lower in [prod.lower() for prod in products]:
                                    self.user_sessions[phone_number]["selected_product"] = text
                                    self.send_product_details(phone_number, text)
                                    self.user_sessions[phone_number]["step"] = "confirmation"
                                    invalid_input = False
                                else:
                                    self.send_text_message(phone_number, "Por favor, selecciona un producto válido.")
                                continue

                            # Manejo del paso "confirmation"
                            if step == "confirmation":
                                if text_lower == "menu_principal":
                                    self.user_sessions[phone_number]["step"] = "category"
                                    self.send_main_menu(phone_number)
                                elif text_lower == "finalizar":
                                    self.create_crm_lead(phone_number)
                                    self.send_text_message(phone_number, "¡Gracias por tu visita! 😊")
                                    del self.user_sessions[phone_number]
                                else:
                                    self.send_text_message(phone_number, "Opción no válida. Usa los botones para seleccionar.")
                                continue

                            if invalid_input:
                                self.send_text_message(phone_number, "No entendí tu mensaje. Escribe 'menu' para ver las opciones.")

                return Response(json.dumps({'status': 'success'}), content_type='application/json', status=200)

            except Exception as e:
                return Response(json.dumps({'error': str(e)}), content_type='application/json', status=500)

    def get_categories(self):
        """Obtiene las categorías únicas desde `category_id` en `product.template`"""
        products = request.env['product.template'].sudo().search([])
        return {product.category_id.name for product in products if product.category_id}
    

    def create_crm_lead(self, phone_number):
        """Crea una oportunidad en el CRM basada en la selección del usuario con más detalles."""
        _logger.info(f"📌 Creando oportunidad en CRM para {phone_number}")

        session = self.user_sessions.get(phone_number, {})

        # Obtener información seleccionada
        category = session.get("selected_category", "No especificada")
        subcategory = session.get("selected_subcategory", "No especificada")
        product_name = session.get("selected_product", "No especificado")

        # Verificar si hay un producto seleccionado
        if product_name == "No especificado":
            self.send_text_message(phone_number, "⚠️ No se ha seleccionado un producto válido para la oportunidad.")
            return

        # Buscar el producto en la base de datos
        product = request.env['product.product'].sudo().search([('name', '=', product_name)], limit=1)

        # Obtener datos del producto
        product_id = product.id if product else None
        product_code = product.default_code if product else "N/A"
        product_price = product.list_price if product else 0.0

        # Crear la descripción detallada
        description = (
            f"📌 *Detalles de la oportunidad:*\n"
            f"📞 *Número de contacto:* {phone_number}\n"
            f"📂 *Categoría:* {category}\n"
            f"📂 *Subcategoría:* {subcategory}\n"
            f"🛒 *Producto:* {product_name}\n"
            f"🆔 *Código del Producto:* {product_code}\n"
            f"💰 *Precio:* ${product_price:.2f}\n"
        )

        # Crear la oportunidad en CRM con los campos adicionales
        lead_vals = {
            "name": f"Oportunidad de {phone_number} - {product_name}",
            "partner_name": f"Cliente WhatsApp {phone_number}",
            "phone": phone_number,
            "description": description,
            "type": "opportunity",
            "selected_product_id": product_id,
            "selected_product_code": product_code,
            "price": product_price,
        }

        # Crear la oportunidad en Odoo
        lead = request.env["crm.lead"].sudo().create(lead_vals)

        if lead:
            _logger.info(f"✅ Oportunidad creada con éxito: {lead.name}")
            self.send_text_message(phone_number, "✅ ¡Oportunidad creada con éxito en nuestro CRM! 🎉")
        else:
            _logger.error("❌ Error al crear la oportunidad en CRM")
            self.send_text_message(phone_number, "❌ Hubo un problema al registrar la oportunidad.")


    def create_crm_lead(self, phone_number):
        """Crea una oportunidad en el CRM basada en la selección del usuario."""
        _logger.info(f"📌 Creando oportunidad en CRM para {phone_number}")

        session = self.user_sessions.get(phone_number, {})

        # Obtener información seleccionada
        category = session.get("selected_category", "No especificada")
        subcategory = session.get("selected_subcategory", "No especificada")
        product = session.get("selected_product", "No especificado")

        # Verificar si hay un producto seleccionado
        if product == "No especificado":
            self.send_text_message(phone_number, "⚠️ No se ha seleccionado un producto válido para la oportunidad.")
            return

        # Crear la oportunidad en CRM
        lead_vals = {
            "name": f"Oportunidad de {phone_number} - {product}",
            "partner_name": f"Cliente WhatsApp {phone_number}",
            "phone": phone_number,
            "description": f"Categoría: {category}\nSubcategoría: {subcategory}\nProducto: {product}",
            "type": "opportunity",
        }

        # Crear la oportunidad en Odoo
        lead = request.env["crm.lead"].sudo().create(lead_vals)

        if lead:
            _logger.info(f"✅ Oportunidad creada con éxito: {lead.name}")
            self.send_text_message(phone_number, "✅ ¡Oportunidad creada con éxito en nuestro sistema de CRM! 🎉")
        else:
            _logger.error("❌ Error al crear la oportunidad en CRM")
            self.send_text_message(phone_number, "❌ Hubo un problema al registrar la oportunidad.")

    
    def send_main_menu(self, phone_number):
        """Muestra el menú principal con las categorías principales."""
        category_names = self.get_categories()
        if not category_names:
            self.send_text_message(phone_number, "No hay categorías con productos disponibles.")
            return

        sections = [{"title": "Categorías", "rows": [{"id": cat, "title": cat} for cat in category_names]}]
        self.send_list_message(phone_number, "Cyrano 🍞", "📌 Selecciona una categoría:", "Ver categorías", sections)

    def get_subcategories_from_category(self, category_name):
        """Obtiene las subcategorías desde `categ_id` filtrando por `category_id`."""
        products = request.env['product.template'].sudo().search([('category_id.name', '=', category_name)])
        return {product.categ_id.name for product in products if product.categ_id}

    def send_subcategories(self, phone_number, category_name):
        """Muestra las subcategorías de la categoría seleccionada."""
        subcategories = self.get_subcategories_from_category(category_name)

        if not subcategories:
            self.send_text_message(phone_number, f"No hay subcategorías disponibles en {category_name}.")
            return

        sections = [{"title": "Subcategorías", "rows": [{"id": subcat, "title": subcat} for subcat in subcategories]}]
        self.send_list_message(phone_number, "Cyrano 🍞", f"📌 Selecciona una subcategoría de {category_name}:", "Ver subcategorías", sections)

    def get_products_from_subcategory(self, subcategory_name):
        """Obtiene los productos de una subcategoría específica."""
        products = request.env['product.template'].sudo().search([('categ_id.name', '=', subcategory_name)])
        return {product.name for product in products}

    def send_product_menu(self, phone_number, subcategory_name):
        """Muestra el menú de productos dentro de la subcategoría seleccionada."""
        products = self.get_products_from_subcategory(subcategory_name)

        if not products:
            self.send_text_message(phone_number, f"No hay productos disponibles en {subcategory_name}.")
            return

        sections = [{"title": "Productos", "rows": [{"id": prod, "title": prod} for prod in products]}]
        self.send_list_message(phone_number, "Cyrano 🍞", f"📌 Productos en {subcategory_name}:", "Ver productos", sections)
    
    
    def send_product_details(self, phone_number, product_name):
        """Muestra el nombre, el precio y la imagen del producto seleccionado."""
        product = request.env['product.template'].sudo().search([('name', '=', product_name)], limit=1)

        if not product:
            self.send_text_message(phone_number, f"No se encontró información para el producto {product_name}.")
            return

        if product.image_url:
            self.send_image_url_message(phone_number, product.image_url, product.name)

        message = f"📦 *{product.name}*\n💰 Precio: ${product.list_price}"
        self.send_text_message(phone_number, message) 
        time.sleep(2)
        self.send_confirmation_buttons(phone_number)

    def send_confirmation_buttons(self, phone_number):
        """Envía botones para regresar al menú principal o finalizar la interacción."""
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": "¿Quieres regresar al menú principal o finalizar la interacción?"
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": "menu_principal",
                                "title": "📜 Menú Principal"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "finalizar",
                                "title": "❌ Finalizar"
                            }
                        }
                    ]
                }
            }
        }
        self.send_whatsapp_message(payload)
        
    def send_image_url_message(self, phone_number, image_url, caption=""):
        """Envía una imagen a través de WhatsApp utilizando una URL válida."""

        if "drive.google.com" in image_url and "/file/d/" in image_url:
            file_id = image_url.split("/file/d/")[1].split("/")[0]
            image_url = f"https://drive.google.com/uc?export=download&id={file_id}"

        access_token = request.env['ir.config_parameter'].sudo().get_param('whatsapp_access_token')
        business_account_id = request.env['ir.config_parameter'].sudo().get_param('whatsapp_business_account_id')

        if not image_url or not image_url.startswith("http"):
            self.send_text_message(phone_number, f"No se pudo cargar la imagen de {caption}.")
            return

        url = f"https://graph.facebook.com/v21.0/{business_account_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "image",
            "image": {
                "link": image_url,
            }
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            _logger.info(f"✅ Imagen enviada con éxito: {caption}")
        else:
            self.send_text_message(phone_number, f"No se pudo enviar la imagen de {caption}.")

    def send_sticker(self, phone_number, sticker_url):
        """Envía un sticker a través de WhatsApp."""
        access_token = request.env['ir.config_parameter'].sudo().get_param('whatsapp_access_token')
        business_account_id = request.env['ir.config_parameter'].sudo().get_param('whatsapp_business_account_id')

        url = f"https://graph.facebook.com/v21.0/{business_account_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "sticker",
            "sticker": {
                "link": sticker_url
            }
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            _logger.info(f"✅ Sticker enviado con éxito: {sticker_url}")
        else:
            _logger.error(f"❌ Error al enviar sticker: {response.text}")

    def send_list_message(self, phone_number, header, body, button, sections):
        """Envía un mensaje interactivo tipo lista."""
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {"type": "text", "text": header},
                "body": {"text": body},
                "action": {"button": button, "sections": sections}
            }
        }
        self.send_whatsapp_message(payload)

    def send_text_message(self, phone_number, message):
        """Envía un mensaje de texto simple a WhatsApp."""
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": message}
        }
        self.send_whatsapp_message(payload)

    def send_whatsapp_message(self, payload):
        """Envía el mensaje a la API de WhatsApp."""
        access_token = request.env['ir.config_parameter'].sudo().get_param('whatsapp_access_token')
        business_account_id = request.env['ir.config_parameter'].sudo().get_param('whatsapp_business_account_id')
        url = f"https://graph.facebook.com/v21.0/{business_account_id}/messages"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

        requests.post(url, headers=headers, json=payload)
