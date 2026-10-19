from odoo import fields, models, api


class AccountTax(models.Model):
    _inherit = 'account.tax'

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields = super()._load_pos_data_fields(config_id)
        fields += ["description", "l10n_pe_edi_tax_code", "invoice_label"]
        return fields