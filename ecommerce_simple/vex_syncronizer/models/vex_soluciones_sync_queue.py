from odoo import models, fields, api

class VexSyncQueue(models.Model):
    _name = 'vex.sync.queue'
    _description = 'Vex Sync Queue'
    _order = 'create_date desc'

    instance_id = fields.Many2one('vex.instance', string='Instance', required=True,
                                  help='Instance to which this sync queue entry belongs')
    action = fields.Selection([
        ('product', 'Product'),
        ('order', 'Order'),
        ('stock', 'Stock'),
        ('image', 'Image')
    ], string='Action', required=True, help='Type of action to be performed in the sync queue')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('error', 'Error')
    ], string='Status', default='pending', required=True, help='Current status of the sync queue entry')
    description = fields.Text(string='Description', help='Detailed description of the action to be performed')
    result = fields.Text(string='Result', help='Result of the action performed, if applicable')
    start_date = fields.Datetime(string='Start Date', help='Date and time when the action started')
    end_date = fields.Datetime(string='End Date', help='Date and time when the action ended')

    @api.model
    def process_meli_sync_queue(self):
        pass    