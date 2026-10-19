from odoo import models, fields
from odoo.exceptions import UserError
from ..services import vex_soluciones_meli_sync

class MeliSyncJob(models.Model):
    _name = 'meli.sync.job'
    _description = 'Job de Sincronización MercadoLibre'

    name = fields.Char(default="Sync ML", readonly=True)
    site_id = fields.Selection([
        ('MLM', 'México'),
        ('MLA', 'Argentina'),
        ('MPE', 'Perú'),
        ('MLC', 'Chile'),
    ], string="Site ID", required=True)

    instance_id = fields.Many2one('meli.instance', string="Instancia", required=True)
    sync_options = fields.Boolean(default=True, string="Opciones ML")
    sync_categories = fields.Boolean(default=True, string="Categorías ML")

    def execute_sync(self):
        for instance in self.env['vex.instance'].search([('store_type','=','mercadolibre')]):
            instance.get_access_token()
            
            access_token = instance.meli_access_token
            env = self.env
            #vex_soluciones_meli_sync.sync_meli_categories(env, instance.meli_country, access_token, instance.id)
            vex_soluciones_meli_sync.sync_meli_options(env, instance.meli_country, access_token, instance.id)
        

                
                
