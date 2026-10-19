import requests
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class WhatsAppCron(models.Model):
    _name = 'whatsapp.cron'
    _description = 'Automated WhatsApp Messaging'

    @api.model
    def send_whatsapp_messages(self):
        _logger.info('Executing send_whatsapp_messages cron job')

        # Obtener credenciales de configuración desde Odoo
        whatsapp_account_id = self.env['ir.config_parameter'].sudo().get_param('whatsapp_business_account_id')
        whatsapp_access_token = self.env['ir.config_parameter'].sudo().get_param('whatsapp_access_token')

        if not whatsapp_account_id or not whatsapp_access_token:
            _logger.error("WhatsApp API credentials are missing. Check system parameters.")
            return

        # Obtener contactos con número de teléfono
        contacts = self.env['res.partner'].search([('phone', '!=', False)])
        if not contacts:
            _logger.info("No contacts with phone numbers found.")
            return

        for contact in contacts:
            phone_number = contact.phone.replace("+", "").replace(" ", "")
            name = contact.name

            _logger.info(f"Sending template message to {name} ({phone_number})")

            url = f"https://graph.facebook.com/v21.0/{whatsapp_account_id}/messages"
            headers = {
                "Authorization": f"Bearer {whatsapp_access_token}",
                "Content-Type": "application/json"
            }

            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "template",
                "template": {
                    "name": "catalogo",
                    "language": {"code": "es"},
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": name}
                            ]
                        }
                    ]
                }
            }

            try:
                response = requests.post(url, headers=headers, json=payload)
                response_json = response.json()

                if response.status_code == 200 and "messages" in response_json:
                    _logger.info(f"Template message sent successfully to {phone_number}")
                else:
                    _logger.error(f"Failed to send template message to {phone_number}: {response_json}")
            except requests.RequestException as e:
                _logger.error(f"Request error sending template message to {phone_number}: {e}")
