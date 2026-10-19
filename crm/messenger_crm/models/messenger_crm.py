import logging
import requests
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class MessengerCRM(models.Model):
    _inherit = 'crm.lead'

    messenger_id = fields.Char(string='Messenger ID')
    is_interested = fields.Boolean(string='Interested', default=False)

    @api.model
    def create_from_messenger(self, messenger_id, message):
        lead = self.create({
            'name': 'Opportunity from Messenger',
            'messenger_id': messenger_id,
            'description': message,
            'stage_id': self.env.ref('crm.stage_lead1').id  # New stage
        })
        return lead

    def mark_as_interested(self):
        self.write({
            'is_interested': True,
            'stage_id': self.env.ref('crm.stage_lead2').id  # Proposition stage
        })

    def send_messenger_message(self, message):
        messenger_id = self.messenger_id
        access_token = self.env['ir.config_parameter'].sudo().get_param('messenger_access_token')

        if not access_token:
            self.message_post(body="Failed to send Messenger message due to missing configuration.")
            return

        url = f"https://graph.facebook.com/v21.0/me/messages?access_token={access_token}"
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "recipient": {
                "id": messenger_id
            },
            "message": {
                "text": message
            }
        }
        response = requests.post(url, headers=headers, json=payload)
        _logger.info(f"Messenger API response: {response.status_code} - {response.text}")
        if response.status_code == 200:
            self.message_post(body="Messenger message sent successfully.")
        else:
            self.message_post(body=f"Failed to send Messenger message. Status code: {response.status_code}, Response: {response.text}")
