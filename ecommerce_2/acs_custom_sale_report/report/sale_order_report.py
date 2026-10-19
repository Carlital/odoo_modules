from odoo import api, models

class SaleOrderReport(models.AbstractModel):
    _name = 'report.acs_custom_sale_report.sale_order_custom_report_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': self.env['sale.order'].browse(docids),
            'company': self.env.company,  # Asegúrate de que la compañía actual se pase al informe
        }