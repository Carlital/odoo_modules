from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import ValidationError, UserError
import requests
from .vex_soluciones_meli_config import COUNTRIES, CURRENCIES, COUNTRIES_DOMINIO
import json
class VexInstance(models.Model):
    _inherit = 'vex.instance'

    store_type = fields.Selection(
        selection_add=[('mercadolibre', 'Mercadolibre')],
        default='mercadolibre',
        ondelete={
            'mercadolibre': 'set default'
        }
    )
    meli_app_id = fields.Char(string="App ID")
    meli_secret_key = fields.Char(string="Secret Key")
    meli_redirect_uri = fields.Char(string="Redirect URI")
    meli_country = fields.Selection(
        [
            ('MLA', 'Argentina'),
            ('MLB', 'Brasil'),
            ('MCO', 'Colombia'),
            ('MCR', 'Costa Rica'),
            ('MEC', 'Ecuador'),
            ('MLC', 'Chile'),
            ('MLM', 'Mexico'),
            ('MLU', 'Uruguay'),
            ('MLV', 'Venezuela'),
            ('MPA', 'Panamá'),
            ('MPE', 'Perú'),
            ('MPT', 'Portugal'),
            ('MRD', 'Dominicana'),
        ],
        string="Meli Country"
    )
    meli_default_currency = fields.Selection(CURRENCIES, string='Default Courrency')

    #meli_default_currency = fields.Many2one('res.currency', string="Default Currency")
    meli_nick = fields.Char(string="Nick")
    meli_user_id = fields.Char(string="User ID")
        # KEYS
    url_get_server_code = fields.Char('Url Get Server Code', compute="get_server_code")
    meli_server_code = fields.Char('Server Code')
    meli_access_token = fields.Char('Access Token',default=' ')
    meli_refresh_token = fields.Char('Refresh Token')
    email_instance = fields.Char("Email")
    meli_introduction = fields.Html('Introduction')
    type_of_commission = fields.Selection(
        [
            ('fixed', 'Fixed'),
            ('percentage', 'Percentage'),
        ],
        string="Type of Commission"
    )
    meli_commission = fields.Float(string="Commission")
    ml_full_warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="MercadoLibre Full Warehouse",
        help="Select the MercadoLibre Full warehouse for this product.",
    )

    ml_full_location_id = fields.Many2one(
        comodel_name="stock.location",
        string="MercadoLibre Full Location",
        domain="[('warehouse_id', '=', ml_full_warehouse_id)]",
        help="Select the MercadoLibre Full location based on the selected warehouse.",
    )

    ml_not_full_warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="MercadoLibre Not Full Warehouse",
        help="Select the MercadoLibre Not Full warehouse for this product.",
    )

    ml_not_full_location_id = fields.Many2one(
        comodel_name="stock.location",
        string="MercadoLibre Not Full Location",
        domain="[('warehouse_id', '=', ml_not_full_warehouse_id)]",
        help="Select the MercadoLibre Not Full location based on the selected warehouse.",
    )

    def get_user(self):
        if not self.meli_nick:
            raise ValidationError('NOT NICK')
        if not self.meli_country:
            raise ValidationError('NOT COUNTRY')
        
        url_user = "https://api.mercadolibre.com/sites/{}/search?nickname={}".format(self.meli_country, self.meli_nick)
        _logger.info("Requesting user info from: %s", url_user)
        item = requests.get(url_user).json()
        _logger.info("Response from user info: %s", item)
        if 'seller' in item:
            self.meli_user_id = str(item['seller']['id'])
        else:
            raise ValidationError(f'INCORRECT NICK OR COUNTRY: {str(item)}')

    @api.depends('meli_redirect_uri','meli_app_id')
    def get_server_code(self):
        for record in self:
            url = ''
            if record.meli_app_id and record.meli_redirect_uri and record.meli_country:
                code_country = COUNTRIES_DOMINIO[record.meli_country]
                url = 'https://auth.mercadolibre.com.{}/authorization?response_type=code&client_id={}&redirect_uri={}'.format(code_country,record.meli_app_id,record.meli_redirect_uri)

            record.url_get_server_code = url

    def get_token(self):               
        store_type = self.env.context.get('store_type')
        _logger.info("Obteniendo token para: %s", store_type)

        if store_type == 'mercadolibre':            
            if not self.meli_server_code:
                raise ValidationError('NOT SERVER CODE')
            if not self.meli_app_id:
                raise ValidationError('Not App ID')
            if not self.meli_secret_key:
                raise ValidationError('Not secret key')
            if not self.meli_redirect_uri:
                raise ValidationError('Not Redirect Uri')
            self.get_access_token()


    def get_access_token(self):
        url = 'https://api.mercadolibre.com/oauth/token?grant_type=authorization_code&client_id={}&client_secret={}&code={}&redirect_uri={}'.format(self.meli_app_id, self.meli_secret_key, self.meli_server_code,self.meli_redirect_uri)

        _logger.info("Obteniendo acces token")
        if self.meli_refresh_token:
            _logger.info("Cambiando a refresh token")
            url = 'https://api.mercadolibre.com/oauth/token'
            data = {
                'grant_type': 'refresh_token',
                'client_id': self.meli_app_id,
                'client_secret': self.meli_secret_key,
                'refresh_token': self.meli_refresh_token  # Usar el refresh_token almacenado en la instancia
            }

            # Realizar la solicitud POST con los parámetros requeridos
            try:
                response = requests.post(url, data=data)
                _logger.info("URL: %s", url)
                if response.status_code == 200:
                    json_obj = json.loads(response.text)
                    if 'access_token' in json_obj:
                        # Actualizar los tokens en la instancia
                        self.write({
                            'meli_access_token': json_obj['access_token'],
                            'meli_refresh_token': json_obj['refresh_token'],
                            
                        })
                        _logger.error(response.text)
                        _logger.info("Token refrescado")
                else:
                    raise UserError(f"Error al refrescar el Access Token. Código de respuesta: {response.status_code} - {response.text}")
            except Exception as ex:
                raise UserError(f"Error al refrescar el Access Token. {ex}")


            return
        try:
            response = requests.post(url)
            _logger.info("URL: %s", url) 
            if response.status_code == 200:
                json_obj = json.loads(response.text)
                if 'access_token' in json_obj:
                    self.write({
                        'meli_access_token': json_obj['access_token'],
                        'meli_refresh_token': json_obj['refresh_token'],
                    })
            else:
                raise UserError(response.text)
        except Exception as ex:
            raise UserError(f"Error al obtener el Access Token.  {ex}")
        
        
    def action_start_sync(self):
        res = super(VexInstance, self).action_start_sync()
        ImportLine = self.env['vex.import_line']
        ProductTemplate = self.env['product.template']

        for instance in self:
            # Buscar línea pendiente solo de esta instancia
            line = ImportLine.search([
                ('status', '=', 'pending'),
                ('action', '=', 'product'),
                ('instance_id', '=', instance.id)
            ], order="create_date asc", limit=1)

            if not line:
                raise UserError(f"No hay líneas pendientes para {instance.name}.")

            if not instance.meli_access_token:
                raise UserError(f"La instancia '{instance.name}' no tiene un token de acceso definido.")

            meli_ids = [x.strip() for x in line.description.split(',') if x.strip()]
            headers = {'Authorization': f'Bearer {instance.meli_access_token}'}

            created = 0
            errors = []

            for meli_id in meli_ids:
                _logger.info(f"Procesando item: {meli_id}")
                try:
                    url = f"https://api.mercadolibre.com/items/{meli_id}?include_attributes=all"
                    response = requests.get(url, headers=headers)
                    if response.status_code != 200:
                        errors.append(f"{meli_id} → HTTP {response.status_code}")
                        continue

                    item_data = response.json()

                    # Buscar o crear categoría
                    categ = self.env['product.category'].search([('name', '=', item_data.get('category_id'))], limit=1)
                    if not categ:
                        categ = self.env['product.category'].create({'name': item_data.get('category_id')})

                    # Preparar y crear producto
                    vals = line._prepare_product_values(
                        item_data=item_data,
                        category_id=categ,
                        image_1920=False,
                        attribute_value_tuples=[],
                        sku_id=False,
                        stock_location_obj='stock',
                        ml_reference='AutoSync',
                        marketplace_fee=0.0,
                        import_line_id=line
                    )
                    self.env['product.template'].create(vals)
                    created += 1

                except Exception as e:
                    errors.append(f"{meli_id} → {str(e)}")

            line.write({
                'status': 'done' if not errors else 'error',
                'result': f'{created} producto(s) creados, {len(errors)} error(es).',
            })
        return res
        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'display_notification',
        #     'params': {
        #         'title': 'Sincronización completada',
        #         'message': f'{created} producto(s) creados. Errores: {len(errors)}',
        #         'type': 'success' if not errors else 'warning',
        #         'sticky': False,
        #     }
        # }

    def start_sync_products(self):
        """
        Método para iniciar la sincronización de productos.
        Este método busca líneas de importación pendientes y las procesa.
        """
        _logger.info("Iniciando sincronización de productos")
        Queue = self.env['vex.sync.queue']
        Queue.process_meli_sync_queue()
    def start_sync_orders(self):
        """
        Método para iniciar la sincronización de órdenes.
        Este método busca órdenes pendientes y las procesa.
        """
        _logger.info("Iniciando sincronización de órdenes")
        Queue = self.env['vex.sync.queue']
        Queue.process_meli_order_queue()