# -*- coding: utf-8 -*-
from odoo import fields, models, api

class VexNotification(models.Model):
    _name = 'vex.notification'
    _description = 'Mercado Libre Notification'

    notification_id = fields.Char(string="Notification ID", required=True)
    topic = fields.Char(string="Topic", required=True)
    resource = fields.Char(string="Resource")
    user_id = fields.Char(string="User ID")
    application_id = fields.Char(string="Application ID")
    sent_date = fields.Datetime(string="Sent Date")
    received_date = fields.Datetime(string="Received Date")
    attempts = fields.Integer(string="Attempts")
    actions = fields.Text(string="Actions")
    raw_data = fields.Text(string="Raw Data", help="Raw JSON body received from the webhook")
    # Relación Many2one con la instancia vex.instance
    instance_id = fields.Many2one('vex.instance', string="Instance", ondelete='cascade', required=True)