
from odoo import api, models, fields
import logging
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        res = super().button_validate()
        if self.origin:
            purchase = self.env['purchase.order'].search(
                [('name', '=', self.origin)])
            if purchase:
                purchase.action_create_invoice()
                if purchase.invoice_ids:
                    for inv in purchase.invoice_ids:
                        journal_id = purchase.journal_id
                        payment_term_id = purchase.payment_term_id
                        if payment_term_id:
                            inv.invoice_payment_term_id = payment_term_id.id
                        inv.invoice_date = fields.Date.today()
                        latam_number = purchase.ref_supplier_serie + '-'+ purchase.ref_supplier_code
                        inv.l10n_latam_document_number = latam_number
                        inv.action_post()
                        if purchase.immediate:
                            payment_wizard_action = inv.action_register_payment()
                            payment_wizard_model = payment_wizard_action.get('res_model')
                            payment_wizard_context = payment_wizard_action.get('context', {})
                            pay_met_line_id = journal_id.inbound_payment_method_line_ids.payment_method_id
                            payment_wizard = self.env[payment_wizard_model].with_context(payment_wizard_context).create({
                                'amount': inv.amount_total,  
                                'journal_id': journal_id.id,
                                'payment_date': fields.Date.today(),
                                'communication': inv.ref,
                            })
                            payment_wizard.action_create_payments()

        return res
