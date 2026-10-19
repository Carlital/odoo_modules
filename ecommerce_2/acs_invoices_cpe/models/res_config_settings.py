from odoo import fields, models, api
import logging
_logger = logging.getLogger(__name__)

class Settings(models.TransientModel):
    _inherit = 'res.config.settings'

    def open_archive_invoices_wizard(self):
        return {
            'name': _('Archivar Facturas sin CPE'),
            'type': 'ir.actions.act_window',
            'res_model': 'archive.invoices.wizard',
            'view_mode': 'form',
            'target': 'new',
        }


class AccountMove(models.Model):
    _inherit = 'account.move'

    active = fields.Boolean(default=True) 