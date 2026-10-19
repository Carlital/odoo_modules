from odoo import models

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_print_invoice_ticket(self):
        """
        Imprime la factura en formato ticket (80 mm de ancho).
        Retorna la acción de reporte para el ticket.
        """
        self.ensure_one()
        try:
            report = self.env['ir.actions.report'].search([
                ('report_name', '=', 'acs_auto_pay_invoice_picking.account_move_ticket_report_template'),
                ('model', '=', 'account.move')
            ], limit=1)
            
            if report:
                return report.report_action(self)
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Reporte no encontrado',
                        'message': 'No se encontró el reporte de ticket para la factura. Verifica que el módulo esté correctamente configurado.',
                        'sticky': False,
                        'type': 'warning',
                    }
                }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error al imprimir',
                    'message': f'No se pudo generar el reporte: {str(e)}',
                    'sticky': False,
                    'type': 'warning',
                }
            }