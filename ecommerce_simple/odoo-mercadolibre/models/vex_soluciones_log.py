# -*- coding: utf-8 -*-
from odoo import fields, models, api

class VexLog(models.Model):
    _name = 'vex.log'
    _description = 'Vex Log'

    name = fields.Char(string='Description')
    level = fields.Selection([
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ], string='Log Level', default='info')
    instance_id = fields.Many2one('vex.instance', string='Instance', required=True)
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    
    @api.model
    def clean_up_logs(self):
        """Elimina los logs antiguos si se supera el límite configurado."""
        instances = self.env['vex.instance'].search([])
        for instance in instances:
            log_limit = instance.log_limit or 10000  # Usar el valor por defecto si no está configurado
            logs = self.search([('instance_id', '=', instance.id)], order='date desc')
            if len(logs) > log_limit:
                logs_to_delete = logs[log_limit:]
                logs_to_delete.unlink()
                instance._log(f"Deleted {len(logs_to_delete)} old logs to maintain the limit of {log_limit} logs.", 'warning')