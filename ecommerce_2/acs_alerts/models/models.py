# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging

_logger = logging.getLogger(__name__)

class acs_alerts(models.Model):
    _name = 'mail.alert'
    _description = 'Mail Alerts'

    name = fields.Char(string='Name')
    
    message_body = fields.Html(
        string='Message Body',
    )

    date = fields.Datetime(
        string='Date',
        default=fields.Datetime.now,
        readonly=True
    )
    
    destinatarios_ids = fields.Many2many( 
        'res.users',
        string='Destinatarios',
    )
    
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('sent', 'Enviado'),
        ('entregado', 'Entregado'),
    ], string='Estado', 
       default='draft', 
       store=True,
       compute='_compute_state'
    )
    
    sent = fields.Boolean(
        string='Enviado?',
        default=False,
    )


    @api.depends('sent')
    def _compute_state(self):
        for record in self:
            if record.sent:
                record.state = 'entregado'
            elif record.sent:
                record.state = 'sent'
            else:
                record.state = 'draft'
            
    def send_alert(self):
        self.ensure_one()        
        for destinatario in self.destinatarios_ids:
            channel = f'progress_update'
            message = {
                'type': 'mail_alert',
                'destinatario_id': destinatario.id,
                'alert_id': self.id,
                'message': self.message_body,
                'name': self.name
            }
            
            try:
                self.env['bus.bus']._sendone('acs_alerts_'+str(destinatario.id), 'acs_alert', message)                
                
            except Exception as e:
                _logger.error(f'Error al enviar alerta a usuario {destinatario.id}: {str(e)}')
                raise
        
        # Marcar la alerta como enviada
        self.write({'sent': True})
        return True