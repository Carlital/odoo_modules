from odoo import models, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_report_values(self, docids, data=None):
        return {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': self.env['sale.order'].browse(docids),
            'company': self.env.company,
        }