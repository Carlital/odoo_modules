from odoo import api, models, fields
from ..services.vex_soluciones_meli_sync import sync_meli_options, sync_meli_categories

class MeliSyncWizard(models.TransientModel):
    _name = 'meli.sync.wizard'
    _description = 'Sincronizar datos ML'

    site_id = fields.Selection([
        ('MLM', 'México'),
        ('MLA', 'Argentina'),
        ('MPE', 'Perú'),
        ('MLC', 'Chile'),
    ], string="Site ID", required=True, default=lambda self: self._get_default_site())

    @api.model
    def _get_default_site(self):
        country = self.env.user.meli_instance_id.meli_country
        site_map = {
            'Mexico': 'MLM',
            'Argentina': 'MLA',
            'Peru': 'MPE',
            'Chile': 'MLC',
        }
        return site_map.get(country, 'MLM')  # Valor por defecto en caso de no coincidir


    sync_options = fields.Boolean(default=True, string="Opciones (condición, tipo, modo)")
    sync_categories = fields.Boolean(default=True, string="Categorías")

    def action_sync(self):
        user = self.env.user
        instance = user.meli_instance_id
        instance.get_access_token()

        access_token = instance.meli_access_token
        env = self.env

        if self.sync_options:
            sync_meli_options(env, self.site_id, access_token)
        if self.sync_categories:
            sync_meli_categories(env, self.site_id, access_token)

        return {'type': 'ir.actions.act_window_close'}