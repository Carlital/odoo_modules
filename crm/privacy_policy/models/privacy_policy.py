from odoo import models, fields

class PrivacyPolicy(models.Model):
    _name = 'privacy.policy'
    _description = 'Privacy Policy'

    name = fields.Char(string='Title', required=True)
    content = fields.Text(string='Content', required=True)
