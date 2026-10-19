from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ArchiveInvoicesWizard(models.TransientModel):
    _name = 'archive.invoices.wizard'
    _description = 'Wizard to Archive Invoices without CPE'

    message = fields.Text(string='Message', default='Archivar facturas sin CPE')

    def archive_invoices(self):
        invoices = self.env['account.move'].sudo().search([
            ('journal_id.type', '=', 'sale'),
            ('journal_id.edi_format_ids', '=', False)
        ])

        if not invoices:
            raise UserError(_('No se encontraron facturas para archivar.'))

        invoices.write({'active': False})

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {
                'message': _('Se han archivado %d facturas.') % len(invoices),
            }
        }