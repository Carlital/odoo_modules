import logging
import requests
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class WhatsAppCRM(models.Model):
    _inherit = 'crm.lead'

    whatsapp_number = fields.Char(string='WhatsApp Number')
    is_interested = fields.Boolean(string='Interested', default=False)

    @api.model
    def create_from_whatsapp(self, number, message):
        lead = self.create({
            'name': 'Opportunity from WhatsApp',
            'phone': number,
            'description': message,
            'stage_id': self.env.ref('crm.stage_lead1').id  # New stage
        })
        return lead

    def mark_as_interested(self):
        self.write({
            'is_interested': True,
            'stage_id': self.env.ref('crm.stage_lead2').id  # Proposition stage
        })

    def send_whatsapp_message(self):
        phone_number = self.phone
        message = self.description
        business_account_id = self.env['ir.config_parameter'].sudo().get_param('whatsapp_business_account_id')
        access_token = self.env['ir.config_parameter'].sudo().get_param('whatsapp_access_token')
        
        if not business_account_id or not access_token:
            self.message_post(body="Failed to send WhatsApp message due to missing configuration.")
            return
        
        url = f"https://graph.facebook.com/v21.0/{business_account_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {
                "body": message
            }
        }
        response = requests.post(url, headers=headers, json=payload)
        _logger.info(f"WhatsApp API response: {response.status_code} - {response.text}")
        if response.status_code == 200:
            self.message_post(body="WhatsApp message sent successfully.")
        else:
            self.message_post(body=f"Failed to send WhatsApp message. Status code: {response.status_code}, Response: {response.text}")

