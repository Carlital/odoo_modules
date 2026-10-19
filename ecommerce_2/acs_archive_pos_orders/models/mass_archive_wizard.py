# acs_archive_pos_orders/models/mass_archive_wizard.py
from odoo import models, fields, api

class PosOrder(models.Model):
    _inherit = 'pos.order'

    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Indica si la orden está archivada.'
    )

class MassArchiveWizard(models.TransientModel):
    _name = 'acs.mass.archive.wizard'
    _description = 'Wizard para Archivar Órdenes de POS Masivamente'

    def action_archive_pos_orders(self):
        # Buscar todas las órdenes de POS que no estén canceladas ni archivadas
        if 'pe_journal_id' in self.env['pos.order'] and 'pe_move_name' in self.env['pos.order']:
            pos_orders = self.env['pos.order'].search([ ('active', '=', True),('pe_journal_id','=',False),('pe_move_name','=',False)])
        else:
            pos_orders = self.env['pos.order'].search([ ('active', '=', True)])
        
        # Marcarlas como archivadas
        if pos_orders:
            pos_orders.write({'active': False})
        
        # Devolver una acción para mostrar el mensaje "Tarea completada"
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Éxito',
                'message': 'Tarea completada',
                'type': 'success',
                'sticky': False,
            }
        }