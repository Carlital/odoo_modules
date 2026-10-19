from odoo import models, fields

class TestDriveConfiguration(models.Model):
    _name = 'test.drive.configuration'
    _description = 'Test Drive Configuration'

    date = fields.Date(string='Date', required=True)
    time = fields.Float(string='Time', required=True)
    available = fields.Boolean(string='Available', default=True)
