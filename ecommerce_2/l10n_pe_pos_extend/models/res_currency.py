from odoo import fields, models, api


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields = super()._load_pos_data_fields(config_id)
        fields += ["currency_unit_label", "currency_subunit_label"]
        return fields
