# -*- coding: utf-8 -*-

import json
import logging

from odoo import api, fields, models, _
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    #reference_ids = fields.One2many('sale.reference', 'sale_id')

    oc_hes_required = fields.Selection(
        selection=[
            ('nothing', 'Nada'),
            ('oc', 'Orden de compra'),
            ('hes', 'HES'),
            ('oc_hes', 'OC y HES'),
        ],
        string='Referencia requerida',
        default='nothing'
    )
    
    # @api.model
    # def _cron_recurring_create_invoice(self):
    #     if self.oc_hes_required == 'nothing':
    #         return self._create_recurring_invoice(automatic=True)
        # if self.oc_hes_required == 'oc':
        #     oc_actual = self.env['sale.reference'].search([('sale_id', '=', self.id), ('reference_doc_type_id.code', '=', '801')],limit=1)
        #     oc_in_invoice = False
        #     invoices = self.env['account_move'].search([('invoice_origin', '=', self.name)])
        #     for invoice in invoices:
                

        

    # def _create_invoices(self, grouped=False, final=False, date=None):

    #     invoices = super()._create_invoices(grouped=grouped, final=final, date=date)

    #     if self.oc_hes_required == 'nothing':
    #         for invoice in invoices:
    #             self.env['l10n_cl.account.invoice.reference'].create({
    #                 'origin_doc_number': self.client_order_ref,
    #                 'l10n_cl_reference_doc_type_id': order_oc.id,
    #                 'reason': 'ORDEN DE COMPRA',
    #                 'date': self.client_order_date,
    #                 'move_id': invoice.id
    #             })

    #             self.env['l10n_cl.account.invoice.reference'].create({
    #                 'origin_doc_number': self.client_hes_ref,
    #                 'l10n_cl_reference_doc_type_id': order_hes.id,
    #                 'reason': 'HOJA DE ENTRADA DE SERVICIOS',
    #                 'date': self.cliente_hes_date,
    #                 'move_id': invoice.id
    #             })
                
    #     return invoices