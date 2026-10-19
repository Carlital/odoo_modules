# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    def get_header_data(self):

        header_data = super().get_header_data()

        _logger.warning('Entro a la funcion y trae los siguientes datos %s', header_data)

        order = self.env['sale.order'].search([
            ('name', '=', self.invoice_origin)
        ], limit =1)

        _logger.warning('Orden de venta que se trae %s', order)

        n2growth = 'N2Growth'

        if order and n2growth.upper() in order.analytic_account_id.name.upper() and self.company_id.id == 4:
            _logger.warning('entro al if')
            header_data['company_logo'] = self.company_id.n2growth_logo

        return header_data