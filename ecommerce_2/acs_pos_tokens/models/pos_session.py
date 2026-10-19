from odoo import models,api

class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.model
    def _load_pos_data_models(self, config_id):
        models = super()._load_pos_data_models(config_id)
        if 'pos.token' not in models:
            models.append('pos.token')
        return models
