# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError, UserError
from odoo.addons.vex_sync_mercado_libre.vex_soluciones_const import COUNTRIES, CURRENCIES, COUNTRIES_DOMINIO, MERCADO_LIBRE_URL
from odoo.http import request
from datetime import datetime

import pytz
import requests
import json
import logging
import urllib.parse
import base64

from typing import List
from odoo import models, fields
import random

_logger = logging.getLogger(__name__)
prefix_mercadolibre = "MLM" #Can be MLA (Mercado libre Argentina, Or in this case MLM Mercado Libre Mexico)

LICENSE_URL = 'https://www.pasarelasdepagos.com'
SECRET_KEY = '587423b988e403.69821411'
    
class VexSolucinesInstaceInherit(models.Model):
    _inherit = "vex.instance"
    _rec_name = "perfil_nickname"
    
    store = fields.Selection(selection_add=[('mercadolibre', 'Mercado Libre')])
    
    # Fields: 'Initial settings'
    meli_app_id = fields.Char('App ID')
    meli_secret_key = fields.Char('Secret Key')
    meli_country = fields.Selection(COUNTRIES, string='Country')
    meli_default_currency = fields.Selection(CURRENCIES, string='Default Courrency')
    meli_redirect_uri = fields.Char('Redirect uri')
    meli_main_instance = fields.Boolean('Main Instance', default=False)
    
    # Fields: 'Keys'
    meli_url_get_server_code = fields.Char('Url Get Server Code')
    meli_server_code = fields.Char('Server Code')
    meli_access_token = fields.Char('Access Token')
    meli_refresh_token = fields.Char('Refresh Token')
    
    # Fields: 'Settings'
    meli_company = fields.Many2one('res.company', string='Company')
    meli_location_id = fields.Many2one('stock.location', string="Stock Location")
   
    license_key = fields.Char("License Key")
    license_valid = fields.Boolean(default=False, string="License Status", readonly=True)
    license_expire = fields.Char(string="License Expiry", readonly=True)

    meli_import_order = fields.Boolean('Order', default=True)
    meli_create_invoice = fields.Boolean('Invoices')
    meli_invoice_status = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')
    ], string='Invoices Status')
    meli_to_bring_order = fields.Selection([
        ('draft', 'Draft'),
        ('order', 'Order')
    ], string='to bring order?', default="draft")
    meli_import_category = fields.Boolean('Category', default=True)
    
    meli_export_product = fields.Boolean('Export Product to Mercado Libre')
    meli_import_product = fields.Boolean('Import Product from Mercado Libre')
    
    # Import price rule
    meli_behavior_price_rule = fields.Selection([
        ('just_in_creation', 'Just in creation'), # Solo en creacion
        ('creation_and_updating', 'Both, creation and updating')
    ], string='Behavior price rule', default="just_in_creation")
    meli_import_price_list = fields.Boolean('Allow price rule for import')
    meli_export_price_list = fields.Boolean('Allow price rule for export')

    meli_import_increase_or_discount = fields.Selection([('increase', 'Increase'),('discount', 'Discount')], string='Increase/Discount for import')
    meli_export_increase_or_discount = fields.Selection([('increase', 'Increase'),('discount', 'Discount')], string='Increase/Discount for export')

    meli_import_type_amount = fields.Selection([('percentage', 'Percentage'),('fixed', 'Fixed')], string='Type amount for import')
    meli_export_type_amount = fields.Selection([('percentage', 'Percentage'),('fixed', 'Fixed')], string='Type amount for export')

    meli_import_amount = fields.Integer('Amount for import')
    meli_export_amount = fields.Integer('Amount for export')

    # Export price rule
    meli_import_product_dropshipping = fields.Boolean('Dropshipping', default=True)
    
    ### Accountant
    # Payments Configuration
    ml_partner_id = fields.Many2one('res.partner', string="Mercado Libre Partner", domain=[('is_company', '=', True)])
    ml_account_journal_id = fields.Many2one('account.journal', string="Account Journal for Mercado Libre", domain=[('currency_id.name', '=', 'MXN')])

    # Automatic Record Payment
    process_payments_customer = fields.Boolean(string="Process payments from Customer")
    process_payments_fee_supplier_ml = fields.Boolean(string="Process payments fee to Supplier ML")
    process_payments_shipping_supplier_ml = fields.Boolean(string="Process payments shipping list cost to Supplier ML")
    
    # Automatización ML a Odoo
    process_all_notifications = fields.Boolean(string="Process all notifications")
    importar_pedidos = fields.Boolean(string="Importar pedidos")
    importar_envios = fields.Boolean(string="Importar envíos")
    importar_clientes = fields.Boolean(string="Importar clientes")
    importar_preguntas = fields.Boolean(string="Importar preguntas")
    search_sku = fields.Boolean(string="Search SKU")
    
    # Automatización Odoo a ML
    actualizar_productos = fields.Boolean(string="Actualizar productos")
    incluir_nuevos_productos = fields.Boolean(string="Incluir nuevos productos")
    publicar_stock = fields.Boolean(string="Publicar Stock")
    publicar_precio = fields.Boolean(string="Publicar Precio")
    
    # Integración con OpenAI
    openai_api_key = fields.Char(string="OpenAI API Key")
    openai_model = fields.Selection([
        ('text-davinci-003', 'Text-DaVinci-003'),
        ('text-curie-001', 'Text-Curie-001'),
        ('text-babbage-001', 'Text-Babbage-001'),
        ('text-ada-001', 'Text-Ada-001')
    ], string="OpenAI Model")
    openai_usage_limit = fields.Integer(string="Usage Limit")
    openai_active = fields.Boolean(string="Enable OpenAI Integration")
    
    # PERFIL
    perfil_id = fields.Char("Perfil ID")  # Campo para almacenar el ID del perfil
    perfil_nickname = fields.Char("Nickname")
    perfil_first_name = fields.Char("First Name")
    perfil_last_name = fields.Char("Last Name")
    perfil_email = fields.Char("Email")
    perfil_country_id = fields.Char("Country ID")
    perfil_phone = fields.Char("Phone")
    perfil_city = fields.Char("City")
    perfil_address = fields.Char("Address")
    perfil_registration_date = fields.Datetime("Registration Date")
    perfil_seller_experience = fields.Char("Seller Experience")
    perfil_user_type = fields.Char("User Type")
    perfil_site_id = fields.Char("Site ID")
    perfil_status_buy_allow = fields.Boolean("Can Buy")
    perfil_status_sell_allow = fields.Boolean("Can Sell")
    perfil_permalink = fields.Char("Permalink")
    
    log_ids = fields.One2many('vex.log', 'instance_id', string='Logs')
    log_limit = fields.Integer(string="Log Limit", default=10000, help="Maximum number of log records to keep.")

    notification_ids = fields.One2many('vex.notification', 'instance_id', string="Notifications")
    notification_limit = fields.Integer(string="Notification Limit", default=10000, help="Maximum number of log records to keep.")

    def name_get(self):
        result = []
        for record in self:
            # Obtener la etiqueta de la selección de store
            store_label = dict(self.fields_get(allfields=['store'])['store']['selection']).get(record.store)
            name = f"{record.perfil_nickname} - {store_label}"
            result.append((record.id, name))
        return result
    
    def _log(self, message, level='info'):
        if True:
            if isinstance(message, list):
                message = ' - '.join(message)
            log_method = getattr(_logger, level, _logger.info)
            log_method(message)
            try:
                print(message)
            except UnicodeEncodeError:
                print(message.encode('utf-8', errors='replace').decode('utf-8'))
            
            try:
                self.env['vex.log'].create({
                    'name': message,
                    'level': level,
                    'instance_id': self.id,
                    'date': fields.Datetime.now(),
                })
            except Exception as ex:
                log_method(f"Error creating log: {str(ex)}")
                
    @api.onchange('store', 'meli_app_id', 'meli_redirect_uri', 'meli_country')
    def _onchange_field(self):
        if self.store == 'mercadolibre':
            if self.meli_app_id and self.meli_redirect_uri and self.meli_country:
                code_country = COUNTRIES_DOMINIO[self.meli_country]
                self.meli_url_get_server_code = f"https://auth.mercadolibre.com.{code_country}/authorization?response_type=code&client_id={self.meli_app_id}&redirect_uri={self.meli_redirect_uri}"
            else:
                self.meli_url_get_server_code = ""
                
    def clear_instance_logs(self):
        self.ensure_one()
        logs = self.env['vex.log'].search([('instance_id', '=', self.id)])
        logs.unlink()
    
    def clear_notifications(self):
        self.ensure_one()
        logs = self.env['vex.notification'].search([('instance_id', '=', self.id)])
        logs.unlink()
                
    def get_auth_code(self):
        self.ensure_one()
        
        # Validar que los campos requeridos no estén vacíos
        if not self.meli_app_id:
            raise UserError("App ID is required.")
        if not self.meli_secret_key:
            raise UserError("Secret Key is required.")
        if not self.meli_country:
            raise UserError("Country is required.")
        if not self.meli_default_currency:
            raise UserError("Default Currency is required.")
        if not self.meli_redirect_uri:
            raise UserError("Redirect URI is required.")
        if not self.meli_url_get_server_code:
            raise UserError("URL Get Server Code is required.")

        # Si todos los campos están completos, proceder con la lógica
        request.session['instance_id'] = self.id
        
        return {
            'type': 'ir.actions.act_url',
            'url': self.meli_url_get_server_code,
            'target': 'new',  
        }
    
    def get_user(self):
        if not self.meli_nick:
            raise ValidationError('NOT NICK')
        if not self.meli_country:
            raise ValidationError('NOT COUNTRY')
        
        url_user = "https://api.mercadolibre.com/sites/{}/search?nickname={}".format(self.meli_country, self.meli_nick)
        
        print(url_user)
        item = requests.get(url_user).json()
        
        if 'seller' in item:
            self.perfil_id = str(item['seller']['id'])
        else:
            raise ValidationError(f'INCORRECT NICK OR COUNTRY: {str(item)}')
        
    def get_perfil(self):
        self.ensure_one()
        url = "https://api.mercadolibre.com/users/me"
        headers = {
            'Authorization': f'Bearer {self.meli_access_token}'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            profile_data = response.json()
            
            # Procesar fecha de registro
            registration_date_str = profile_data.get('registration_date')
            registration_date = None
            if registration_date_str:
                try:
                    registration_date = datetime.strptime(registration_date_str, "%Y-%m-%dT%H:%M:%S.%f%z")
                    registration_date = registration_date.astimezone(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    self._log(f"Failed to parse registration date: {registration_date_str}", 'error')
            
            # Descargar y codificar la imagen
            image_data = None
            thumbnail_url = profile_data.get('thumbnail', {}).get('picture_url')
            if thumbnail_url:
                try:
                    image_response = requests.get(thumbnail_url)
                    if image_response.status_code == 200:
                        image_data = base64.b64encode(image_response.content)
                    else:
                        self._log(f"Failed to download image: {thumbnail_url}", 'error')
                except requests.RequestException as e:
                    self._log(f"Error downloading image: {str(e)}", 'error')

            self.write({
                'perfil_id': str(profile_data.get('id')),  # Guardar el ID del perfil
                'perfil_nickname': profile_data.get('nickname'),
                'perfil_first_name': profile_data.get('first_name'),
                'perfil_last_name': profile_data.get('last_name'),
                'perfil_email': profile_data.get('email'),
                'perfil_country_id': profile_data.get('country_id'),
                'perfil_phone': profile_data.get('phone', {}).get('number'),
                'perfil_city': profile_data.get('address', {}).get('city'),
                'perfil_address': profile_data.get('address', {}).get('address'),
                'perfil_registration_date': registration_date,
                'perfil_seller_experience': profile_data.get('seller_experience'),
                'perfil_user_type': profile_data.get('user_type'),
                'perfil_site_id': profile_data.get('site_id'),
                'perfil_status_buy_allow': profile_data.get('status', {}).get('buy', {}).get('allow'),
                'perfil_status_sell_allow': profile_data.get('status', {}).get('sell', {}).get('allow'),
                'perfil_permalink': profile_data.get('permalink'),
                'image': image_data,  # Guardar la imagen
            })
            self._log("Perfil actualizado correctamente.", 'info')
        except requests.exceptions.RequestException as e:
            self._log(f"Error al obtener el perfil: {str(e)}", 'error')
            raise UserError(f"Error al obtener el perfil: {str(e)}")
        except Exception as ex:
            self._log(f"Error inesperado: {str(ex)}", 'error')
            raise UserError(f"Error inesperado: {str(ex)}")
        
    def write_perfil(self):
        self.ensure_one()
        if not self.perfil_id or not self.meli_access_token:
            raise UserError("Perfil ID y Access Token son requeridos para actualizar el perfil.")

        # Definir la URL correctamente antes de su uso
        url = f"https://api.mercadolibre.com/users/{self.perfil_id}"
        
        payload = json.dumps({
            "address": self.perfil_address,
            # "state": self.perfil_country_id, api -> address.state
            "state": "MX-DIF",
            "city": self.perfil_city,
            "zip_code": "1431",  # Suponiendo que este valor es constante o lo obtienes de otra fuente
            "phone": {
                "area_code": "011",  # Suponiendo que este valor es constante o lo obtienes de otra fuente
                "number": self.perfil_phone,
                "extension": "001"  # Suponiendo que este valor es constante o lo obtienes de otra fuente
            },
            "first_name": self.perfil_first_name,
            "last_name": self.perfil_last_name,
            "company": {
                "corporate_name": "Acme",
                "brand_name": "Acme Company"
            },
            "mercadoenvios": "accepted"  # Ajusta según tu lógica de negocio
        })
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.meli_access_token}'
        }

        # Registrar los datos que se van a enviar
        self._log(f"Enviando datos a {url} con el siguiente payload: {payload}", 'info')
        self._log(f"Encabezados: {headers}", 'info')

        try:
            # Realizar la solicitud
            response = requests.put(url, headers=headers, data=payload)
            response.raise_for_status()
            self._log("Perfil actualizado exitosamente en Mercado Libre.", 'info')
            self.get_perfil()
            return response.json()
        except requests.exceptions.RequestException as e:
            self._log(f"Error al actualizar el perfil: {str(e)}", 'error')
            raise UserError(f"Error al actualizar el perfil: {str(e)}")
        except Exception as ex:
            self._log(f"Error inesperado: {str(ex)}", 'error')
            raise UserError(f"Error inesperado: {str(ex)}")
    
    def clear_perfil(self):
        self.ensure_one()

        # Verificar credenciales necesarias
        if not self.meli_access_token or not self.meli_app_id:
            raise UserError("Access Token y Application ID son necesarios para eliminar la aplicación.")

        url = f"https://api.mercadolibre.com/users/{self.perfil_id}/applications/{self.meli_app_id}"
        headers = {
            'Authorization': f'Bearer {self.meli_access_token}'
        }

        try:
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            self._log(f"Aplicación eliminada exitosamente para el usuario {self.perfil_id}.", 'info')
            
            # Limpiar los datos del perfil y credenciales
            self.write({
                'perfil_id': False,
                'perfil_nickname': False,
                'perfil_first_name': False,
                'perfil_last_name': False,
                'perfil_email': False,
                'perfil_country_id': False,
                'perfil_phone': False,
                'perfil_city': False,
                'perfil_address': False,
                'perfil_registration_date': False,
                'perfil_seller_experience': False,
                'perfil_user_type': False,
                'perfil_site_id': False,
                'perfil_status_buy_allow': False,
                'perfil_status_sell_allow': False,
                'perfil_permalink': False,
                'image': False,

                'meli_server_code': False,
                'meli_access_token': False,
                'meli_refresh_token': False,
            })
            self.status_auth = "unauthenticated"
            self._log("Perfil y credenciales de autenticación limpiados correctamente.", 'info')

            # Inicializar cron_model
            cron_model = self.env['ir.cron'].sudo()
            
            # Obtener el ID del modelo
            model_id = self.env['ir.model'].sudo().search([('model', '=', 'vex.instance')], limit=1).id
            
            # Verificar si quedan instancias autenticadas
            authenticated_instances = self.env['vex.instance'].sudo().search_count([('status_auth', '=', 'authenticated')])

            if authenticated_instances == 0:
                # Eliminar el cron job asociado con la instancia
                cron_job = cron_model.search([
                    ('model_id', '=', model_id),
                    ('code', '=', 'model.refresh_token_all()')
                ], limit=1)
                
                if cron_job:
                    cron_job.unlink()
                    self._log("Cron job general para refrescar todos los tokens eliminado correctamente.", 'info')
                else:
                    self._log("No se encontró ningún cron job general para refrescar todos los tokens.", 'info')
            else:
                self._log("No se puede eliminar el cron job, hay instancias autenticadas.", 'warning')

            # Verificar si queda algún cron job activo para el modelo 'vex.instance'
            remaining_crons = cron_model.search([
                ('model_id', '=', model_id)
            ])
            
            if not remaining_crons:
                self._log("No quedan cron jobs activos para el modelo 'vex.instance'.", 'info')

        except requests.exceptions.RequestException as e:
            # Manejo de errores en la solicitud
            self._log(f"Error al eliminar la autentificación: {str(e)}", 'error')
            raise UserError(f"Error al eliminar la autentificación: {str(e)}")

            
    def get_access_token(self):
        # Validaciones de campos
        if not self.meli_app_id:
            self._log('Not App ID', 'error')
            raise ValidationError('Not App ID')
        if not self.meli_secret_key:
            self._log('Not secret key', 'error')
            raise ValidationError('Not secret key')
        if not self.meli_redirect_uri:
            self._log('Not Redirect Uri', 'error')
            raise ValidationError('Not Redirect Uri')
        if not self.meli_server_code:
            self._log('Not Server Code', 'error')
            raise ValidationError('Not Server Code')
        
        # Construir la URL y el payload
        url = 'https://api.mercadolibre.com/oauth/token'
        payload = {
            'grant_type': 'authorization_code',
            'client_id': self.meli_app_id,
            'client_secret': self.meli_secret_key,
            'code': self.meli_server_code,
            'redirect_uri': self.meli_redirect_uri
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        self._log(f"Sending POST request to {url}", 'info')
        self._log(f"Headers: {headers}", 'info')
        self._log(f"Payload: {payload}", 'info')

        try:
            # Enviar la solicitud POST
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()  # Esto lanza una excepción para códigos de estado 4xx/5xx
            self._log(f"Response status code: {response.status_code}", 'info')
            self._log(f"Response content: {response.content}", 'info')

            json_obj = response.json()
            access_token = json_obj.get('access_token')
            refresh_token = json_obj.get('refresh_token')
            
            if access_token:
                self._log(f"Access token obtained: {access_token}", 'info')
                self.write({
                    'meli_access_token': access_token,
                    'meli_refresh_token': refresh_token,
                })
            else:
                try:
                    error_response = response.json()
                    error_message = error_response.get('message', 'Unknown error occurred')
                    self._log(f"Error response: {error_response}", 'error')
                    raise UserError(f"Error obtaining access token: {error_message}")
                except (ValueError, KeyError):
                    self._log(f"Unexpected error format in response: {response.content}", 'error')
                    raise UserError("Unexpected error format in response.")
        except requests.exceptions.RequestException as e:
            self._log(f"Request error: {str(e)}", 'error')
            raise UserError(f"Error obtaining access token: {str(e)}")
        except Exception as ex:
            self._log(f"Unexpected error: {str(ex)}", 'error')
            raise UserError(f"Unexpected error: {str(ex)}")
        
    def refresh_token(self):
        self.ensure_one()
        if not self.meli_app_id or not self.meli_secret_key or not self.meli_refresh_token:
            raise UserError("App ID, Client Secret, y Refresh Token son requeridos para refrescar el token.")

        url = f"https://api.mercadolibre.com/oauth/token?grant_type=refresh_token&client_id={self.meli_app_id}&client_secret={self.meli_secret_key}&refresh_token={self.meli_refresh_token}"
        
        payload = {}
        headers = {
            'Content-Type': 'application/json'
        }

        # Registrar los datos que se van a enviar
        self._log(f"Solicitando refresh token con la siguiente URL: {url}", 'info')

        try:
            # Realizar la solicitud
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            response_data = response.json()
            
            # Actualizar los tokens en el registro de la instancia
            self.meli_access_token = response_data.get('access_token')
            new_refresh_token = response_data.get('refresh_token')
            if new_refresh_token:
                self.meli_refresh_token = new_refresh_token
            
            self._log("Token de acceso actualizado exitosamente en Mercado Libre.", 'info')
        except requests.exceptions.RequestException as e:
            self._log(f"Error al refrescar el token: {str(e)}", 'error')
            raise UserError(f"Error al refrescar el token: {str(e)}")
        except Exception as ex:
            self._log(f"Error inesperado: {str(ex)}", 'error')
            raise UserError(f"Error inesperado: {str(ex)}")
        
    def refresh_token_all(self):
        # Buscar todas las instancias que están autenticadas
        instances = self.search([('status_auth', '=', 'authenticated')])

        for instance in instances:
            try:
                # Llamar al método de refrescar token de cada instancia
                instance.refresh_token()
                instance._log(f"Token de acceso refrescado exitosamente para la instancia {instance.id} - {instance.perfil_nickname}.", 'info')
            except UserError as e:
                instance._log(f"Error al refrescar el token para la instancia {instance.id} - {instance.perfil_nickname}: {str(e)}", 'error')
            except Exception as e:
                instance._log(f"Error inesperado al refrescar el token para la instancia {instance.id} - {instance.perfil_nickname}: {str(e)}", 'error')
                # Asegurarse de que el error no cause que la transacción falle
                # instance.env.cr.rollback()
            
    def valid_license_key(self):
        BASE_URL = self.env['ir.config_parameter'].sudo().get_param('web.base.url').replace('http://', '').replace('https://', '')
        URL_CHECK = f"{LICENSE_URL}/?slm_action=slm_check&license_key={self.license_key}&registered_domain={BASE_URL}&secret_key={SECRET_KEY}"
        URL_ACTIVATE = f"{LICENSE_URL}/?slm_action=slm_activate&license_key={self.license_key}&registered_domain={BASE_URL}&secret_key={SECRET_KEY}"
        HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}
        
        parsed_url = urllib.parse.urlparse(BASE_URL)
        self._log(f"LICENSE_URL: {LICENSE_URL}", level='debug')
        self._log(f"license_key: {self.license_key}", level='debug')
        self._log(f"SECRET_KEY: {SECRET_KEY}", level='debug')
        self._log(f"BASE_URL_PARSE: {parsed_url.netloc}", level='debug')

        if not self.license_key:
            self._log("Ingrese todos los datos.", level='error')
            self.license_valid = False
            return

        URL = f"{LICENSE_URL}?license_key={self.license_key}&slm_action=slm_check&secret_key={SECRET_KEY}&registered_domain={parsed_url.netloc}"

        self._log(f"Request URL: {URL}", level='debug')
        self._log(f"Request headers: {HEADERS}", level='debug')

        try:
            r = requests.get(url=URL, headers=HEADERS)
            r.raise_for_status()  # Raise an error for non-200 status codes
            response_json = r.json()  # Try to parse JSON
        except requests.exceptions.RequestException as e:
            self._log(f"Error making request: {e}", level='error')
            self.license_valid = False
            return
        except json.JSONDecodeError as e:
            self._log(f"Error decoding JSON response: {e}", level='error')
            self._log(f"Response content: {r.text}", level='error')
            self.license_valid = False
            return

        self._log(f"Response JSON: {response_json}", level='info')

        # Check if the response contains the expected keys
        if 'result' in response_json:
            if response_json['result'] != 'success':
                self._log("False", level='info')
                self.license_valid = False
            else:
                self._log("True", level='info')
                self.license_valid = True
        else:
            self._log("Else False", level='info')
            self.license_valid = False
            
    # IMPORTATION MIGRATION
    def validate_meli_token(self):
        self._log(f'----validate_meli_token-----', level='debug')
        obj = {
            'success': False,
            'msg': '',
        }

        headers = {
            'Content-Type': "application/json",
            'Authorization': f'Bearer {self.meli_access_token}'
        }

        # URL para la validación del token
        url_validate = f"https://api.mercadolibre.com/sites/{self.perfil_site_id}/categories"
        
        # Log de inicio de validación
        self._log(f'Validating token with URL: {url_validate}', level='info')

        try:
            # Realiza la solicitud GET
            validated_request = requests.get(url=url_validate, headers=headers)
            # Log de respuesta de solicitud
            self._log(f'Response status code: {validated_request.status_code}', level='info')

            # Verifica el código de estado de la respuesta
            if validated_request.status_code == 401 or validated_request.status_code != 200:
                # Token inválido, intenta obtener un nuevo token
                self._log('Token is invalid or unauthorized, attempting to refresh token...', level='warning')
                validate_token = self.get_access_token()

                if not validate_token:
                    obj['success'] = False
                    obj['msg'] = "unauthorized - invalid access token" + " " + self.name
                    self._log(f'Failed to refresh token. Message: {obj["msg"]}', level='error')
                else:
                    obj['success'] = True
                    self._log('Token refreshed successfully.', level='info')

            if validated_request.status_code == 200:
                obj['success'] = True
                self._log('Token is valid.', level='info')

        except requests.RequestException as e:
            self._log(f'Exception occurred: {e}', level='error')

        return obj
        
            
    def import_instance(self):
        self.action_toggle_is_synchronizing()
        validate_token = self.validate_meli_token()  # Correcta llamada al método
        self._log(f"validate_token: {validate_token}")
        
        if not validate_token['success']:
            self._log(f"No se pudo actualizar el token, verifique las credenciales.")
            return  # Salir si el token no es válido
        
        headers = {
            'Content-Type': "application/json",
            'Authorization': f'Bearer {self.meli_access_token}'
        }
        
        self.get_product_sku(headers)
        
    def notify_feature_in_development(self):
        self.ensure_one()
        message = (
            "🚧 Esta función está en construcción! 🚧\n\n"
            "Por favor, vuelva más tarde. Estamos trabajando para mejorar su experiencia. "
            "¡Gracias por su paciencia! 😊"
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',  
            'params': {
                'title': 'Función en Desarrollo',
                'message': message,
                'type': 'info',  # Puede ser 'info', 'warning', 'danger', 'success'
                'sticky': False,  # True/False para hacer la notificación persistente
            },
        }

    def get_orders_by_seller_id(self, id: int, limit: int = 50, offset: int = 0) -> List[dict]:
        url = f"https://api.mercadolibre.com/orders/search?seller={id}&limit={limit}&offset={offset}"
        headers = {
            'Authorization': f'Bearer {self.meli_access_token}'
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            self._log(response.text)
            self._log(response.json()) 
        except requests.RequestException as e:
            self._log(f"Error al obtener órdenes: {str(e)}", level='error')
            raise UserError(f"Error al obtener órdenes: {str(e)}")
        
        return response.json()

    def import_orders_by_seller(self):
        self.ensure_one()
        self._log("Iniciando la importación de órdenes desde Mercado Libre")

        orders_data = self.get_orders_by_seller_id(self.perfil_id)
        paging = orders_data.get('paging', {})
        total = paging.get('total', 0)
        offset = paging.get('offset', 0)
        limit = paging.get('limit', 0)
        orders = orders_data.get('results', [])

        SaleOrder = self.env['sale.order']
        Partner = self.env['res.partner']
        Product = self.env['product.product']
        Currency = self.env['res.currency']
        Pricelist = self.env['product.pricelist']
        Payment = self.env['account.payment']
        Account_move = self.env['account.move']

        while total > offset:
            for order in orders:
                try:
                    order_id = order.get('id')
                    
                    # Verificar si la orden ya fue importada
                    if SaleOrder.search([('meli_order_id', '=', order_id)]):
                        self._log(f"La orden {order_id} ya fue importada previamente.")
                        continue

                    buyer_info = order.get('buyer', {})
                    buyer_nickname = buyer_info.get('nickname')
                    total_amount = order.get('total_amount')
                    currency_id = order.get('currency_id', 'USD')
                    mediations = order.get('mediations', []) # Esto es un arreglo de objetos OjO
                    self._log(f'Mediations -> {mediations}')
                    order_items = order.get('order_items', [])
                    mediations_ids = [str(mediation.get('id')) for mediation in mediations]
                    sale_fee = sum([item.get('sale_fee', 0) for item in order_items])
                    shipping_id = order.get('shipping', {}).get('id', 0)
                    shipment_data = self.get_shipment(shipping_id)
                    context_info = order.get('context', {})
                    channel = context_info.get('channel', 'unknown')  # Asignar 'unknown' si no está disponible

                    self._log([
                        f"Orden ID: {order_id}",
                        f"Buyer Nickname: {buyer_nickname}",
                        f"Total Amount: {total_amount}",
                        f"Currency: {currency_id}",
                        f"Channel: {channel}"  # Añadir el valor del canal al log, ahora tenemos que guardarlo
                    ])

                    partner = Partner.search([('name', '=', buyer_nickname)], limit=1)
                    if partner:
                        partner = self.update_client_data_by_id(buyer_info["id"])
                    else:
                        partner = self.create_client_by_id(buyer_info["id"])

                    # Buscar la moneda en Odoo
                    currency = Currency.search([('name', '=', currency_id)], limit=1)
                    if not currency:
                        raise UserError(f"La moneda {currency_id} no está configurada en el sistema.")

                    # Buscar o crear la lista de precios para la moneda
                    pricelist = Pricelist.search([('currency_id', '=', currency.id)], limit=1)
                    if not pricelist:
                        # Crear una nueva lista de precios para la moneda si no existe
                        pricelist = Pricelist.create({
                            'name': f'Tarifa Mercado Libre',
                            'currency_id': currency.id
                        })

                    sale_order = SaleOrder.create({
                        'partner_id': partner.id,
                        'amount_total': total_amount,  # Ajustar según sea necesario
                        'currency_id': currency.id,
                        'pricelist_id': pricelist.id,
                        'origin': f'Mercado Libre {order_id}',
                        'state': 'draft',
                        'meli_order_id': order_id,
                        'meli_channel' : channel
                    })

                    self.update_order_status(sale_order, order)
                    self.update_mediations_by_ids(mediations_ids, sale_order.id)
                    # Create payment transaction
                    payment_method_id = self.env.ref('account.account_payment_method_manual_out').id
                    journal_id = 8


                    ml_taxes_payment = Payment.create({
                        'payment_type': 'outbound',
                        'payment_method_id': payment_method_id,
                        'partner_type': 'customer',
                        'partner_id': partner.id,
                        'amount': sale_fee,
                        'currency_id': currency.id,
                        'journal_id': journal_id,
                    })

                    void_payment = Payment.create({
                        'payment_type': 'inbound',
                        'payment_method_id': payment_method_id,
                        'partner_type': 'customer',
                        'partner_id': partner.id,
                        'amount': total_amount - sale_fee,
                        'currency_id': currency.id,
                        'journal_id': journal_id,
                    })

                    ml_taxes_movement = Account_move.search([('payment_id', '=', ml_taxes_payment.id)], limit=1)
                    void_movement = Account_move.search([('payment_id', '=', void_payment.id)], limit=1)
                    ml_taxes_movement.ref = f'Taxes-{sale_order.name}'
                    void_movement.ref = f'Utility-{sale_order.name}'
                    # If the order requires shipping, create a shipping cost payment
                    shipping_movement = None
                    if shipment_data:
                        self._log(f"Creating shipping payment for order {order_id}")
                        shipment_cost = shipment_data.get('shipping_option', {}).get('cost', 0)
                        shipping_payment = Payment.create({
                            'payment_type': 'outbound',
                            'payment_method_id': payment_method_id,
                            'partner_type': 'customer',
                            'partner_id': partner.id,
                            'amount': shipment_cost,
                            'currency_id': currency.id,
                            'journal_id': journal_id,
                        })
                        shipping_movement = Account_move.search([('payment_id', '=', shipping_payment.id)], limit=1)
                        shipping_movement.ref = f'Shipping-{sale_order.name}'
                    # Update the status of the movements
                    self.update_movement_status(order,ml_taxes_movement, void_movement, shipping_movement)
                    
                    for item in order_items:
                        product_title = item.get('item', {}).get('title', 'Producto sin título')
                        quantity = item.get('quantity', 1)
                        unit_price = item.get('unit_price', 0)

                        product = Product.search([('name', '=', product_title)], limit=1)
                        if not product:
                            product = Product.create({
                                'name': product_title,
                                'list_price': unit_price,
                            })

                        sale_order.write({
                            'order_line': [(0, 0, {
                                'product_id': product.id,
                                'product_uom_qty': quantity,
                                'price_unit': unit_price,
                            })]
                        })

                except Exception as ex:
                    self._log(f"Error al procesar la orden {order.get('id')}: {str(ex)}", level='error')
                    continue
            
            offset += limit
            orders_data = self.get_orders_by_seller_id(self.perfil_id, limit=limit, offset=offset)

        self._log("Importación de órdenes completada.")
    
    # ITEMS

    def get_items_ids_by_seller_id(self, id: int, limit: int = 100, offset: int = 0) -> List[str]:
        url = f"https://api.mercadolibre.com/users/{id}/items/search?limit={limit}&offset={offset}"
        headers = {
            'Authorization': f'Bearer {self.meli_access_token}'
        }
        total = 999999
        items = []

        while total > offset:
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
            except requests.RequestException as e:
                self._log(f"Error al obtener artículos: {str(e)}", level='error')
                raise UserError(f"Error al obtener artículos: {str(e)}")

            items_data = response.json()
            items += items_data.get('results', [])
            paging = items_data.get('paging', {})
            total = paging.get('total', 0)
            offset = paging.get('offset', 0) + limit
        self._log(f"Total de artículos encontrados: {len(items)}")
        return items

    def get_items(self) -> List[dict]:
        item_ids = self.get_items_ids_by_seller_id(self.perfil_id)
        total = len(item_ids)
        offset = 0
        limit = 20
        items = []

        headers = {
            'Authorization': f'Bearer {self.meli_access_token}'
        }

        while total > offset:
            items_ids_chunk = item_ids[offset:offset+limit]

            details_url = f"https://api.mercadolibre.com/items?ids={','.join(items_ids_chunk)}"
            try:
                details_response = requests.get(details_url, headers=headers)
                details_response.raise_for_status()
                items_details = details_response.json()
                items += items_details
            except requests.RequestException as e:
                self._log(f"Error al obtener detalles de artículos: {str(e)}", level='error')
                raise UserError(f"Error al obtener detalles de artículos: {str(e)}")
            
            offset += limit
        self._log(f"Total de detalles de artículos obtenidos: {len(items)}")
        return items

    def import_items(self):
        self.ensure_one()
        self._log("Iniciando la importación de artículos desde Mercado Libre")

        items_data = self.get_items()

        ProductTemplate = self.env['product.template']
        self._log(f"Importando {len(items_data)} artículos a Odoo")
        for item_detail in items_data:
            item_data = item_detail.get('body', {})
            item_id = item_data.get('id')
            if not item_id:
                continue

            existing_product = ProductTemplate.search([('meli_id', '=', item_id)], limit=1)
            if existing_product:
                self._log(f"El artículo {item_id} ya está registrado en el sistema.")
                continue

            currency_code = item_data.get('currency_id', 'MXN').upper()
            currency = self.env['res.currency'].search([('name', '=', currency_code)], limit=1)

            if not currency:
                self._log(f"Moneda {currency_code} no encontrada. No se creará el producto {item_id}.", level='error')
                continue

            category_id = item_data.get('category_id', '')
            odoo_category_id = self.import_category_recursive_v2(category_id)

            if not odoo_category_id:
                self._log(f"Categoría con ID Mercado Libre {category_id} no encontrada. Omitiendo.")
                continue

            thumbnail_url = item_data.get('thumbnail', '')
            image_data = None
            if thumbnail_url:
                try:
                    image_response = requests.get(thumbnail_url)
                    if image_response.status_code == 200:
                        image_data = base64.b64encode(image_response.content)
                    else:
                        self._log(f"Failed to download image: {thumbnail_url}", 'error')
                except requests.RequestException as e:
                    self._log(f"Error downloading image: {str(e)}", 'error')

            try:
                new_product = ProductTemplate.create({
                    'name': item_data.get('title', f'Producto {item_id}'),
                    'meli_id': item_id,
                    'list_price': item_data.get('price', 0.0),
                    'default_code': item_data.get('id', ''),
                    'currency_id': currency.id,
                    'meli_categ_id': odoo_category_id if odoo_category_id else 1,
                    'image_1920': image_data,  # Thumbnail
                    'detailed_type': 'product',
                    'responsible_id': self.env.user.id or None,
                    'purchase_method': 'purchase',
                    'instance_id': self.id,
                    # INFO
                    'meli_permalink': item_data.get('permalink', ''),
                    'meli_catalog_product_id': item_data.get('catalog_product_id', None),
                    'meli_catalog_listing': item_data.get('catalog_listing', False),
                    'meli_accepts_mercadopago': item_data.get('accepts_mercadopago', False),
                    'meli_status': item_data.get('status', None),
                    'meli_warranty': item_data.get('warranty', False),
                })
                
                new_product.assign_tags(item_data.get('tags', []))
                new_product.assign_channels(item_data.get('channels', []))
                new_product.assign_existing_attributes(item_data.get('attributes', []))
                
                available_quantity = item_data.get('available_quantity', 0)
                warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)
                if warehouse:
                    self.env['stock.quant'].with_context(inventory_mode=True).create({
                        'product_id': new_product.product_variant_id.id,
                        'location_id': warehouse.lot_stock_id.id,
                        'inventory_quantity': available_quantity,
                    })._apply_inventory()

                self._log(f"Artículo {item_id} importado correctamente.")
            except Exception as ex:
                self._log(f"Error al procesar el artículo {item_id}: {str(ex)}", level='error')

        self._log("Importación de artículos completada.")

    def update_item_by_sku(self, sku: str):
        self.ensure_one()
        # Obtén el ID del administrador
        admin_user_id = self.env.ref('base.user_admin').id
        self = self.with_user(admin_user_id)
        self._log(f"Iniciando la importación del artículo con SKU {sku} desde Mercado Libre")
        
        url = f"{MERCADO_LIBRE_URL}/items/{sku}"
        headers = {
            'Authorization': f'Bearer {self.meli_access_token}'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            self._log(f"Error al obtener el artículo: {str(e)}", level='error')
            self._log(f"El artículo con SKU {sku} ha sido eliminado en Mercado Libre. Eliminando de la base de datos de Odoo.")
            self.delete_item_by_sku(sku)
            return 
        
        item_data = response.json()
        item_id = item_data.get('id')
        status = item_data.get('status')
        sub_status = item_data.get('sub_status', [""])
        self._log(f"Estado del artículo {item_id}: {status} ({sub_status})")

        if status == 'closed' and 'deleted' in sub_status:
            self._log(f"El artículo con SKU {sku} ha sido eliminado en Mercado Libre. Eliminando de la base de datos de Odoo.")
            self.delete_item_by_sku(sku)
            return
        
        ProductTemplate = self.env['product.template'].sudo().search([('meli_id', '=', sku)], limit=1)

        if not ProductTemplate:
            self._log(f"El artículo con SKU {sku} no está registrado en el sistema. No se puede actualizar, en cambio se creara", level='error')
            self.create_item_by_sku(sku)
            return
        
        currency_code = item_data.get('currency_id', 'MXN').upper()
        currency = self.env['res.currency'].sudo().search([('name', '=', currency_code)], limit=1)
        if not currency:
            self._log(f"Moneda {currency_code} no encontrada. No se creará el producto {item_id}.", level='error')
            return
        
        category_id = item_data.get('category_id', '')
        odoo_category_id = self.import_category_recursive_v2(category_id)
        if not odoo_category_id:
            self._log(f"Categoría con ID Mercado Libre {category_id} no encontrada. Asignando categoría por defecto.")
            return
        
        thumbnail_url = item_data.get('thumbnail', '')
        image_data = None
        if thumbnail_url:
            try:
                image_response = requests.get(thumbnail_url)
                if image_response.status_code == 200:
                    image_data = base64.b64encode(image_response.content)
                else:
                    self._log(f"Failed to download image: {thumbnail_url}", 'error')
            except requests.RequestException as e:
                self._log(f"Error downloading image: {str(e)}", 'error')
        
        try:
            ProductTemplate.write({
                'name': item_data.get('title', f'Producto {item_id}'),
                'meli_id': item_id,
                'list_price': item_data.get('price', 0.0),
                'default_code': item_data.get('id', ''),
                'currency_id': currency.id,
                'meli_categ_id': odoo_category_id if odoo_category_id else 1,
                'image_1920': image_data,
                'detailed_type': 'product',
                'responsible_id': self.env.user.id,
                'purchase_method': 'purchase',
                'instance_id': self.id,
                # INFO
                'meli_permalink': item_data.get('permalink', ''),
                'meli_catalog_product_id': item_data.get('catalog_product_id', None),
                'meli_catalog_listing': item_data.get('catalog_listing', False),
                'meli_accepts_mercadopago': item_data.get('accepts_mercadopago', False),
                'meli_status': item_data.get('status', None),
                'meli_warranty': item_data.get('warranty', False),
            })
            
            self.update_stocks_by_skus([sku])
            
            ProductTemplate.assign_tags(item_data.get('tags', []))
            ProductTemplate.assign_channels(item_data.get('channels', []))
            ProductTemplate.assign_existing_attributes(item_data.get('attributes', []))
            
            pictures = item_data.get('pictures', [])
            image_gallery = []
            for picture in pictures:
                picture_url = picture.get('secure_url') or picture.get('url')
                if picture_url:
                    try:
                        picture_response = requests.get(picture_url)
                        if picture_response.status_code == 200:
                            image_data = base64.b64encode(picture_response.content)
                            # actualizar para evitar sobre uso de db
                            attachment = self.env['ir.attachment'].create({
                                'name': picture_url.split('/')[-1],
                                'datas': image_data,
                                'type': 'binary',
                                'res_model': 'product.template',
                                'res_id': ProductTemplate.id,
                                'mimetype': 'image/jpeg',
                            })
                            image_gallery.append(attachment.id)
                        else:
                            self._log(f"Failed to download image: {picture_url}", 'error')
                    except requests.RequestException as e:
                        self._log(f"Error downloading image: {str(e)}", 'error')
            
            if image_gallery:
                ProductTemplate.write({'image_gallery_ids': [(6, 0, image_gallery)]})
            
            self._log(f"Artículo {item_id} importado correctamente.")
        except Exception as ex:
            self._log(f"Error al procesar el artículo {item_id}: {str(ex)}", level='error')
        
        self._log("Importación del artículo completada.")
    
    def delete_item_by_sku(self, sku: str):
        self.ensure_one()
        self._log(f"Iniciando la eliminación del artículo con SKU {sku} desde la base de datos de Odoo")
        
        # Buscar el producto en la base de datos de Odoo utilizando el SKU
        product = self.env['product.template'].search([('meli_id', '=', sku)], limit=1)
        
        if not product:
            self._log(f"No se encontró el artículo con SKU {sku}. No se puede borrar", level='error')
            return
        
        try:
            # Eliminar el producto de la base de datos
            product.unlink()
            self._log(f"Artículo con SKU {sku} eliminado correctamente.")
        except Exception as e:
            self._log(f"Error al eliminar el artículo con SKU {sku}: {str(e)}", level='error')
            raise UserError(f"Error al eliminar el artículo con SKU {sku}: {str(e)}")
        
        self._log("Eliminación del artículo completada.")
    
    def create_item_by_sku(self, sku: str):
        self.ensure_one()
        self._log(f"Iniciando la importación del artículo con SKU {sku} desde Mercado Libre")
        
        url = f"{MERCADO_LIBRE_URL}/items/{sku}"
        headers = {
            'Authorization': f'Bearer {self.meli_access_token}'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            self._log(f"Error al obtener el artículo: {str(e)}", level='error')
            raise UserError(f"Error al obtener el artículo: {str(e)}")
        
        item_data = response.json()
        item_id = item_data.get('id')
        
        ProductTemplate = self.env['product.template'].sudo().search([('meli_id', '=', sku)], limit=1)

        if ProductTemplate:
            self._log(f"El artículo con SKU {sku} ya está registrado en el sistema. No se creará.", level='error')
            return
        
        
        currency_code = item_data.get('currency_id', 'MXN').upper()
        currency = self.env['res.currency'].sudo().search([('name', '=', currency_code)], limit=1)
        if not currency:
            self._log(f"Moneda {currency_code} no encontrada. No se actualizara, en cambio se creara el producto {item_id}.", level='error')
            return
                
        category_id = item_data.get('category_id', '')
        odoo_category_id = self.import_category_recursive_v2(category_id)
        if not odoo_category_id:
            self._log(f"Categoría con ID Mercado Libre {category_id} no encontrada. Asignando categoría por defecto.")
            return
        
        thumbnail_url = item_data.get('thumbnail', '')
        image_data = None
        if thumbnail_url:
            try:
                image_response = requests.get(thumbnail_url)
                if image_response.status_code == 200:
                    image_data = base64.b64encode(image_response.content)
                else:
                    self._log(f"Failed to download image: {thumbnail_url}", 'error')
            except requests.RequestException as e:
                self._log(f"Error downloading image: {str(e)}", 'error')
        
        try:
            new_product = self.env['product.template'].sudo().create(
                {
                'name': item_data.get('title', f'Producto {item_id}'),
                'meli_id': item_id,
                'list_price': item_data.get('price', 0.0),
                'default_code': item_data.get('id', ''),
                'currency_id': currency.id,
                'meli_categ_id': odoo_category_id if odoo_category_id else 1,
                'image_1920': image_data,
                'detailed_type': 'product',
                'responsible_id': self.env.user.id,
                'purchase_method': 'purchase',
                'instance_id': self.id,
                # INFO
                'meli_permalink': item_data.get('permalink', ''),
                'meli_catalog_product_id': item_data.get('catalog_product_id', None),
                'meli_catalog_listing': item_data.get('catalog_listing', False),
                'meli_accepts_mercadopago': item_data.get('accepts_mercadopago', False),
                'meli_status': item_data.get('status', None),
                'meli_warranty': item_data.get('warranty', False),
            })

            self.update_stocks_by_skus([sku])
            
            new_product.assign_tags(item_data.get('tags', []))
            new_product.assign_channels(item_data.get('channels', []))
            new_product.assign_existing_attributes(item_data.get('attributes', []))
            
            pictures = item_data.get('pictures', [])
            image_gallery = []
            for picture in pictures:
                picture_url = picture.get('secure_url') or picture.get('url')
                if picture_url:
                    try:
                        picture_response = requests.get(picture_url)
                        if picture_response.status_code == 200:
                            image_data = base64.b64encode(picture_response.content)
                            attachment = self.env['ir.attachment'].sudo().create({
                                'name': picture_url.split('/')[-1],
                                'datas': image_data,
                                'type': 'binary',
                                'res_model': 'product.template',
                                'res_id': new_product.id,
                                'mimetype': 'image/jpeg',
                            })
                            image_gallery.append(attachment.id)
                        else:
                            self._log(f"Failed to download image: {picture_url}", 'error')
                    except requests.RequestException as e:
                        self._log(f"Error downloading image: {str(e)}", 'error')
            
            if image_gallery:
                new_product.write({'image_gallery_ids': [(6, 0, image_gallery)]})
            
            self._log(f"Artículo {item_id} importado correctamente.")
        except Exception as ex:
            self._log(f"Error al procesar el artículo {item_id}: {str(ex)}", level='error')
        
        self._log("Importación del artículo completada.")
    # END ITEMS

    # ORDERS
    def get_order_by_id(self, order_id: str):
        self.ensure_one()
        self._log(f"Iniciando la importación de la orden con ID {order_id} desde Mercado Libre")

        url = f"{MERCADO_LIBRE_URL}/orders/{order_id}"
        headers = {
            'Authorization': f'Bearer {self.meli_access_token}'
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            self._log(f"Error al obtener la orden: {str(e)}", level='error')
            return

        order_data = response.json()
        self._log(order_data)
        return order_data

    def get_order_status(self, mercado_libre_order):
        self.ensure_one()
        self._log(f"Iniciando la obtención del estado de la orden {mercado_libre_order.get('id')}")
        status = mercado_libre_order.get('status', 'draft')
        draft_statuses = [
            "confirmed",         # Estado inicial de un orden; aún sin haber sido pagada.
            "payment_required",  # Es necesario que se confirme el pago de la orden necesita para mostrar la información del usuario.
            "payment_in_process",# Existe un pago relacionado con la orden, pero aún no se acreditó.
            "partially_paid",    # La orden tiene un pago asociado acreditado, pero no es suficiente.
            'approved',          # La orden fue aprobada por el vendedor.
        ]
        done_statuses = [
            "paid",              # La orden tiene un pago asociado acreditado.
        ]
        cancelled_statuses = [
            "cancelled",         # La orden fue cancelada.
        ]
        other_statuses = [
            "partially_refunded",# La orden tiene devoluciones parciales de los pagos.
            "pending_cancel",    # Cuando se quiere cancelar la orden pero nos cuesta devolver el pago.
        ]
        self._log(f"Estado de la orden {mercado_libre_order.get('id')}: {status}")
        if status in draft_statuses:
            return 'draft'
        elif status in done_statuses:
            return 'done'
        elif status in cancelled_statuses:
            return 'cancel'
        elif status in other_statuses:
            return status

    def update_order_status(self, order_instance, mercado_libre_order):
        self.ensure_one()
        status = self.get_order_status(mercado_libre_order)
        self._log(f"Actualizando estado de la orden de {order_instance.state} a {status}")
        try: 
            if status == 'draft':
                order_instance.write({'state': 'draft'})
            elif status == 'done':
                order_instance.action_quotation_sent()
                self._log(f"Confirming order")
                order_instance.action_confirm()
            elif status == 'cancel':
                order_instance.write({'state': 'cancel'})
            elif status:
                order_instance.write({'state': status})
            else:
                self._log(f"Estado de la orden no reconocido: {status}", level='warning')
                
        except Exception as ex:
            self._log(f"Error al actualizar el estado de la orden: {str(ex)}", level='error')
            raise UserError(f"Error al actualizar el estado de la orden: {str(ex)}")

    def create_order(self, order_data):
        self.ensure_one()
        # Obtén el ID del administrador
        admin_user_id = self.env.ref('base.user_admin').id
        self = self.with_user(admin_user_id)
        order_id = order_data.get('id')
        sale_fee = sum([item.get('sale_fee', 0) for item in order_data.get('order_items', [])])
        self._log(f"Iniciando la importación de la orden con ID {order_id} desde Mercado Libre")
        
        SaleOrder = self.env['sale.order']
        Partner = self.env['res.partner']
        Product = self.env['product.product']
        Currency = self.env['res.currency']
        Pricelist = self.env['product.pricelist']
        # PaymentTransaction = self.env['payment.transaction']
        Payment = self.env['account.payment']

        try:

            if SaleOrder.search([('meli_order_id', '=', order_id)]):
                self._log(f"La orden {order_id} ya fue importada previamente.")
                return
            
            buyer_info = order_data.get('buyer', {})
            buyer_nickname = buyer_info.get('nickname')
            total_amount = order_data.get('total_amount')
            currency_id = order_data.get('currency_id', 'USD')
            mediations = order_data.get('mediations', [])
            mediations_ids = [str(mediation.get('id')) for mediation in mediations]
            shipment_data = self.get_shipment(order_data.get('shipping', {}).get('id', 0))

            self._log([
                f"Orden ID: {order_id}",
                f"Buyer Nickname: {buyer_nickname}",
                f"Total Amount: {total_amount}",
                f"Currency: {currency_id}"
            ])

            partner = Partner.search([('name', '=', buyer_nickname)], limit=1)
            if not partner:
                partner = Partner.create({
                    'name': buyer_nickname,
                    'customer_rank': 1
                })

            currency = Currency.search([('name', '=', currency_id)], limit=1)
            if not currency:
                raise UserError(f"La moneda {currency_id} no está configurada en el sistema.")
            
            pricelist = Pricelist.search([('currency_id', '=', currency.id)], limit=1)
            if not pricelist:
                pricelist = Pricelist.create({
                    'name': f'Tarifa Mercado Libre',
                    'currency_id': currency
                })
            
            sale_order = SaleOrder.create({
                'partner_id': partner.id,
                'amount_total': total_amount,
                'currency_id': currency.id,
                'pricelist_id': pricelist.id,
                'origin': f'Mercado Libre {order_id}',
                'state': 'draft', # hacer diccionario 
                'meli_order_id': order_id,
            })

            payment_method_id = self.env.ref('account.account_payment_method_manual_out').id
            journal_id = 9

            Account_move = self.env['account.move']

            ml_taxes_payment = Payment.create({
                'payment_type': 'outbound',
                'payment_method_id': payment_method_id,
                'partner_type': 'customer',
                'partner_id': partner.id,
                'amount': sale_fee,
                'currency_id': currency.id,
                'journal_id': journal_id,
            })

            void_payment = Payment.create({
                'payment_type': 'inbound',
                'payment_method_id': payment_method_id,
                'partner_type': 'customer',
                'partner_id': partner.id,
                'amount': total_amount - sale_fee,
                'currency_id': currency.id,
                'journal_id': journal_id,
            })
            shipping_movement = None
            if shipment_data:
                self._log(f"Creating shipping payment for order {order_id}")
                shipping_cost = shipment_data.get('shipping_option', {}).get('cost', 0)
                shipping_payment = Payment.create({
                    'payment_type': 'outbound',
                    'payment_method_id': payment_method_id,
                    'partner_type': 'customer',
                    'partner_id': partner.id,
                    'amount': shipping_cost,
                    'currency_id': currency,
                    'journal_id': journal_id,
                })
                shipping_movement = Account_move.search([('payment_id', '=', shipping_payment.id)], limit=1)
                shipping_movement.ref = f'Shipping-{sale_order.name}'
            
            ml_taxes_movement = Account_move.search([('payment_id', '=', ml_taxes_payment.id)], limit=1)
            void_movement = Account_move.search([('payment_id', '=', void_payment.id)], limit=1)
            ml_taxes_movement.ref = f'Taxes-{sale_order.name}'
            void_movement.ref = f'Utility-{sale_order.name}'
            
            self.update_movement_status(order_data,ml_taxes_movement, void_movement, shipping_movement)

            order_items = order_data.get('order_items', [])
            products_to_update_stock = [order["item"]["id"] for order in order_items]
            
            self.update_order_status(sale_order, order_data)
            self.update_mediations_by_ids(mediations_ids, sale_order.id)
            self.update_stocks_by_skus(products_to_update_stock)

            for item in order_items:
                product_title = item.get('item', {}).get('title', 'Producto sin título')
                quantity = item.get('quantity', 1)
                unit_price = item.get('unit_price', 0)

                product = Product.search([('name', '=', product_title)], limit=1)
                if not product:
                    product = Product.create({
                        'name': product_title,
                        'list_price': unit_price,
                    })

                sale_order.write({
                    'order_line': [(0, 0, {
                        'product_id': product.id,
                        'product_uom_qty': quantity,
                        'price_unit': unit_price,
                    })]
                })


        except Exception as ex:
            self._log(f"Error al procesar la orden {order_id}: {str(ex)}", level='error')
            raise UserError(f"Error al procesar la orden {order_id}: {str(ex)}")
        
        self._log("Importación de la orden completada.")

    def update_order(self, order_data):
        self.ensure_one()
        # Obtén el ID del administrador
        admin_user_id = self.env.ref('base.user_admin').id
        self = self.with_user(admin_user_id)

        order_id = order_data.get('id')
        self._log(f"Iniciando la actualización de la orden con ID {order_id} desde Mercado Libre")
        
        SaleOrder = self.env['sale.order']
        Partner = self.env['res.partner']
        Currency = self.env['res.currency']
        Pricelist = self.env['product.pricelist']
        Account_move = self.env['account.move']

        try:
            sale_to_update = SaleOrder.search([('meli_order_id', '=', order_id)])
            if not sale_to_update:
                self._log(f"La orden {order_id} no ha sido importada previamente.")
                return
            
            buyer_info = order_data.get('buyer', {})
            buyer_nickname = buyer_info.get('nickname')
            total_amount = order_data.get('total_amount')
            currency_id = order_data.get('currency_id', 'USD')
            mediations = order_data.get('mediations', []) # Esto es un arreglo de objetos OjO
            mediations_ids = [str(mediation.get('id')) for mediation in mediations]

            self._log([
                f"Orden ID: {order_id}",
                f"Buyer Nickname: {buyer_nickname}",
                f"Total Amount: {total_amount}",
                f"Currency: {currency_id}"
            ])

            partner = Partner.search([('name', '=', buyer_nickname)], limit=1)
            if not partner:
                raise UserError(f"El comprador {buyer_nickname} no está registrado en el sistema.")

            # Buscar la moneda en Odoo
            currency = Currency.search([('name', '=', currency_id)], limit=1)
            if not currency:
                raise UserError(f"La moneda {currency_id} no está configurada en el sistema.")

            # Buscar o crear la lista de precios para la moneda
            pricelist = Pricelist.search([('currency_id', '=', currency.id)], limit=1)
            if not pricelist:
                raise UserError(f"La lista de precios para la moneda {currency_id} no está configurada en el sistema.")
            
            sale_to_update.write({
                'partner_id': partner.id,
                'amount_total': total_amount,
                'currency_id': currency.id,
                'pricelist_id': pricelist.id,
                'origin': f'Mercado Libre {order_id}',
                'meli_order_id': order_id,
            })

            order_items = order_data.get('order_items', [])
            products_to_update_stock = [order["item"]["id"] for order in order_items]
            
            # update order transaction
            ml_taxes_movement = Account_move.search([('ref', '=', f'Taxes-{sale_to_update.name}')], limit=1)
            void_movement = Account_move.search([('ref', '=', f'Utility-{sale_to_update.name}')], limit=1)
            shipment_movement = Account_move.search([('ref', '=', f'Shipping-{sale_to_update.name}')], limit=1)

            self._log(f"Buscando transacción con referencia {sale_to_update.name}")
            if ml_taxes_movement and void_movement:
                self._log(f"Movimientos encontrados: {ml_taxes_movement}, {void_movement}")
                self.update_movement_status(order_data, ml_taxes_movement, void_movement, shipment_movement)

            self.update_order_status(sale_to_update, order_data)
            self.update_mediations_by_ids(mediations_ids, sale_to_update.id)
            self.update_stocks_by_skus(products_to_update_stock)

            
        except Exception as ex:
            self._log(f"Error al procesar la orden {order_data.get('id')}: {str(ex)}", level='error')
            raise UserError(f"Error al procesar la orden {order_data.get('id')}: {str(ex)}")

        self._log("Actualización de la orden completada.")
    # END ORDERS
    # MOVEMENTS
    def update_movement_status(self, order_data, ml_taxes_movement, void_movement, shipment_movement = None):
        self.ensure_one()
        status = self.get_order_status(order_data)
        self._log(f"Actualizando estado de la transacción de {ml_taxes_movement.state} a {status}")
        try: 
            if status == 'draft':
                ml_taxes_movement.write({'state': 'draft'})
                void_movement.write({'state': 'draft'})
                if shipment_movement:
                    shipment_movement.write({'state': 'draft'})
            elif status == 'done':
                ml_taxes_movement._post()
                void_movement._post()
                if shipment_movement:
                    shipment_movement._post()
            elif status == 'cancel':
                ml_taxes_movement.write({'state': 'cancel'})
                void_movement.write({'state': 'cancel'})
                if shipment_movement:
                    shipment_movement.write({'state': 'cancel'})
            else:
                self._log(f"Estado de la transacción {ml_taxes_movement.name}, {void_movement.name} no reconocido: {status}", level='warning')
        except Exception as ex:
            self._log(f"Error al actualizar el estado de la transacción: {str(ex)}", level='error')
    # END MOVEMENTS
    # STOCKS
    def update_stocks_by_skus(self, skus: List[str]):
        self.ensure_one()
        # Obtén el ID del administrador
        admin_user_id = self.env.ref('base.user_admin').id
        self = self.with_user(admin_user_id)
        self._log(f"Iniciando la actualización de stocks para los SKUs: {', '.join(skus)}")

        for sku in skus:
            url = f"{MERCADO_LIBRE_URL}/items/{sku}"
            headers = {
                'Authorization': f'Bearer {self.meli_access_token}'
            }

            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
            except requests.RequestException as e:
                self._log(f"Error al obtener stock para el SKU {sku}: {str(e)}", level='error')
                return
            
            product_to_update = self.env['product.template'].sudo().search([('meli_id', '=', sku)], limit=1)
            if not product_to_update:
                self._log(f"Producto con SKU {sku} no encontrado en Odoo. No se puede actualizar el stock.", level='error')
                return
            
            product_data = response.json()

            actual_stock_quantity = product_data.get('available_quantity', 0)
            warehouse = self.env['stock.warehouse'].sudo().search([('company_id', '=', self.env.company.id)], limit=1)
            if warehouse:
                self.env['stock.quant'].with_context(inventory_mode=True).create({
                    'product_id': product_to_update.product_variant_id.id,
                    'location_id': warehouse.lot_stock_id.id,
                    'inventory_quantity': actual_stock_quantity,
                })._apply_inventory()

            self._log(f"Stock actualizado para el SKU {sku}. Cantidad: {actual_stock_quantity}")
    # END STOCKS
    # MEDIATIONS
    def update_mediations_by_ids(self, mediations_ids: List[str], order_id: int) -> dict:
        self.ensure_one()
        # Obtén el ID del administrador
        admin_user_id = self.env.ref('base.user_admin').id
        self = self.with_user(admin_user_id)
        self._log("Obteniendo detalles de mediaciones")

        updated_mediations_counter = 0
        created_mediations_counter = 0

        for mediation_id in mediations_ids:
            # {{BASE_URL}}/post-purchase/v1/claims/5288895882
            url = f"{MERCADO_LIBRE_URL}/post-purchase/v1/claims/{mediation_id}"
            headers = {
                'Authorization': f'Bearer {self.meli_access_token}'
            }
            try:
                response = requests.get(url, headers=headers)
            except Exception as ex:
                self._log(f"Error al obtener detalles de mediaciones: {str(ex)}")
                pass

            if response.status_code != 200:
                self._log(f"Error al obtener detalles de mediaciones: {response.content}")
                pass
            else:
                try: 
                    mediation = json.loads(response.text)
                    players = mediation['players']
                    buyer = next((player for player in players if player['type'] in ['buyer','receiver']), None)
                    seller = next((player for player in players if player['type'] in ['seller', 'sender']), None)
                    self._log(f"Detalles de mediaciones: {mediation}")

                    date_str = mediation['date_created']
                    date_obj = datetime.strptime(date_str.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                    resolution = mediation['resolution']
                    reason = resolution['reason'] if resolution else None


                    obj = {}
                    obj['meli_order_id'] = order_id
                    obj['meli_mediation_id'] = mediation['id']
                    obj["meli_recourse_id"] = mediation["resource_id"]
                    obj['meli_mediation_status'] = mediation['status']
                    obj['meli_mediation_type'] = mediation['type']
                    obj['meli_mediation_reason_id'] = mediation['reason_id']
                    obj['meli_mediation_quantity_type'] = mediation['quantity_type']
                    obj['meli_mediation_buyer_id'] = buyer['user_id']
                    obj['meli_mediation_seller_id'] = seller['user_id']
                    obj['meli_resolution_reason'] = reason
                    obj['meli_resolution_date'] = date_obj.strftime('%Y-%m-%d %H:%M:%S')
                    self._log(f"Objeto a crear: {obj}")
                except Exception as ex:
                    self._log(f"Error al destructurar detalles de mediaciones, key: {str(ex)}")
                    continue

                domain = []
                domain.append(('meli_mediation_id', '=', mediation['id']))
                existing_mediation = self.env['vex.meli.mediation'].sudo().search(domain)

                if existing_mediation:
                    print("La mediacion ya existe")
                    updated_mediations_counter += 1
                    # actualizamos la mediacion 
                    existing_mediation.write(obj)
                else:
                    try:
                        created_mediations_counter += 1
                        mediation_id = self.env['vex.meli.mediation'].sudo().create(obj)
                    except Exception as ex:
                        self._log(f"Error al crear mediaciones: {str(ex)}")
                        continue
            
        return {'updated_mediations': updated_mediations_counter, 'created_mediations': created_mediations_counter}
    # END MEDIATIONS 

    # CATEGORIES
    def import_categoria(self):
        self.ensure_one()
        self._log("Iniciando la importación de categorías desde Mercado Libre")

        url = f"https://api.mercadolibre.com/sites/{self.perfil_site_id}/categories"
        headers = {
            'Authorization': f'Bearer {self.meli_access_token}'
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            self._log(f"Error al obtener categorías: {str(e)}", level='error')
            raise UserError(f"Error al obtener categorías: {str(e)}")

        categories_data = response.json()
        ProductCategory = self.env['product.category']

        for category in categories_data:
            category_id = category.get('id')
            category_name = category.get('name')

            if not category_id or not category_name:
                continue

            existing_category = ProductCategory.search([('name', '=', category_name)], limit=1)

            if existing_category:
                self._log(f"La categoría '{category_name}' ya existe en Odoo.")
                parent_category = existing_category
            else:
                parent_category = ProductCategory.create({
                    'name': category_name,
                    'complete_name': f"{self.perfil_site_id}/{category_name}",
                    'meli_category_id': category_id,

                })
                self._log(f"Categoría '{category_name}' importada correctamente.")

            # Importar subcategorías
            subcategories_url = f"https://api.mercadolibre.com/categories/{category_id}"
            try:
                subcategories_response = requests.get(subcategories_url, headers=headers)
                subcategories_response.raise_for_status()
                subcategories_data = subcategories_response.json()
            except requests.RequestException as e:
                self._log(f"Error al obtener subcategorías para '{category_name}': {str(e)}", level='error')
                continue

            children_categories = subcategories_data.get('children_categories', [])
            for child_category in children_categories:
                child_category_id = child_category.get('id')
                child_category_name = child_category.get('name')

                if not child_category_id or not child_category_name:
                    continue

                existing_child_category = ProductCategory.search([('name', '=', child_category_name)], limit=1)

                if existing_child_category:
                    self._log(f"La subcategoría '{child_category_name}' ya existe en Odoo.")
                else:
                    ProductCategory.create({
                        'name': child_category_name,
                        'parent_id': parent_category.id,
                        'complete_name': f"{self.perfil_site_id}/{category_name}/{child_category_name}",
                        'meli_category_id': child_category_id,
                    })
                    self._log(f"Subcategoría '{child_category_name}' importada correctamente.")

        self._log("Importación de categorías y subcategorías completada.")
    
    def import_category_recursive(self, category_id):
        """Importa la categoría y sus subcategorías de forma recursiva."""
        ProductCategory = self.env['product.category']

        # Obtener los detalles de la categoría para path_from_root
        try:
            category_details_response = requests.get(f"https://api.mercadolibre.com/categories/{category_id}", headers={
                'Authorization': f'Bearer {self.meli_access_token}'
            })
            category_details_response.raise_for_status()
            category_details = category_details_response.json()
        except requests.RequestException as e:
            self._log(f"Error al obtener detalles para la categoría ID '{category_id}': {str(e)}", level='error')
            return

        # Obtener nombre de la categoría actual y path_from_root
        category_name = category_details.get('name', 'Sin Nombre')
        path_from_root = category_details.get('path_from_root', [])
        complete_name = "/".join([item['name'] for item in path_from_root]) if path_from_root else category_name

        # Determinar si es categoría final
        is_final_category = len(path_from_root) == 3  # Asumiendo que la estructura es Padre/Subpadre/Hijo

        # Obtener el ID de la categoría padre en Odoo, si existe
        parent_id = None
        if len(path_from_root) > 1:
            # Buscar la categoría padre basada en el id de path_from_root
            parent_meli_id = path_from_root[-2]['id']
            parent_category = ProductCategory.search([('meli_category_id', '=', parent_meli_id)], limit=1)
            parent_id = parent_category.id if parent_category else None

        # Buscar o crear la categoría en Odoo
        existing_category = ProductCategory.search([('meli_category_id', '=', category_id)], limit=1)
        if existing_category:
            self._log(f"La categoría '{category_name}' ya existe en Odoo.")
            odoo_category = existing_category
        else:
            odoo_category = ProductCategory.create({
                'name': category_name,
                'meli_category_id': category_id,
                'parent_id': parent_id,
                'complete_name': complete_name,
            })
            self._log(f"Categoría '{category_name} - {category_id}' importada correctamente.")

        if is_final_category:
            # No hay subcategorías para procesar
            return odoo_category.id

        # Procesar subcategorías
        children_categories = category_details.get('children_categories', [])
        for child_category in children_categories:
            child_category_id = child_category.get('id')

            if not child_category_id:
                continue

            # Llamar recursivamente para importar la subcategoría
            # self.import_category_recursive(child_category_id)

        return

    def action_show_fake_trends(self):
        # Datos ficticios de ejemplo
        fake_trends = [
            {'keyword': 'ejemplo 1', 'url': 'https://mercadolibre.com.mx/ejemplo-1'},
            {'keyword': 'ejemplo 2', 'url': 'https://mercadolibre.com.mx/ejemplo-2'},
            {'keyword': 'ejemplo 3', 'url': 'https://mercadolibre.com.mx/ejemplo-3'},
            {'keyword': 'ejemplo 4', 'url': 'https://mercadolibre.com.mx/ejemplo-4'},
            {'keyword': 'ejemplo 5', 'url': 'https://mercadolibre.com.mx/ejemplo-5'},
        ]
        # Mostrar el wizard con las tendencias ficticias
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tendencias (Prueba)',
            'view_mode': 'form',
            'res_model': 'trend.wizard',
            'target': 'new',
            'context': {
                'default_category_id': self.id,
                'default_trends': [(0, 0, {
                    'keyword': trend['keyword'],
                    'url': trend['url']
                }) for trend in fake_trends]
            }
        }


    def action_show_trends(self, meli_category_id , id):
        # Datos ficticios de ejemplo
        # self.meli_access_token

        url = f"{MERCADO_LIBRE_URL}/trends/{prefix_mercadolibre}/{meli_category_id}"
        headers = {
            'Authorization': f'Bearer {self.meli_access_token}'
        }

        fake_trends = [
            {'keyword': prefix_mercadolibre, 'url': self.meli_access_token},
            {'keyword': meli_category_id, 'url': 'https://mercadolibre.com.mx/ejemplo-2'},
            {'keyword': 'ejemplo 3', 'url': 'https://mercadolibre.com.mx/ejemplo-3'},
            {'keyword': 'ejemplo 4', 'url': 'https://mercadolibre.com.mx/ejemplo-4'},
            {'keyword': 'ejemplo 5', 'url': 'https://mercadolibre.com.mx/ejemplo-5'},
        ]

        try:            
            # Agrega logging para depuración
            _logger.info(f"URL de la solicitud: {url}")
            _logger.info(f"Headers de la solicitud: {headers}")
       
            answered = requests.get(url, headers=headers)
            answered.raise_for_status()
            
            _logger.info(f"Respuesta exitosa")
            _logger.info(f"Respuesta de la API: {answered.status_code}")
            _logger.info(f"Contenido de la respuesta: {answered.text}")
            fake_trends = json.loads(answered.content)
          
            #return True
             
        except requests.RequestException as e:
            self._log(f"Error al responder la pregunta: {str(e)}", level='error')
            # Agrega logging para verificar la respuesta
            _logger.info(f"Respuesta de la API: {answered.status_code}")
            _logger.info(f"Contenido de la respuesta: {answered.text}")
            return False


        
        # Mostrar el wizard 
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tendencias ',
            'view_mode': 'form',
            'res_model': 'trend.wizard',
            'target': 'new',
            'context': {
                'default_category_id': id,
                'default_trends': [(0, 0, {
                    'keyword': trend['keyword'],
                    'url': trend['url']
                }) for trend in fake_trends]
            }
        } 
    
    def import_category_recursive_v2(self, category_id):
        """Importa la categoría y sus subcategorías de forma recursiva."""
        ProductCategory = self.env['product.category']

        # Buscar o crear la categoría en Odoo
        existing_category = ProductCategory.search([('meli_category_id', '=', category_id)], limit=1)
        if existing_category:
            odoo_category = existing_category
            return odoo_category.id

        # Obtener los detalles de la categoría para path_from_root
        try:
            category_details_response = requests.get(f"https://api.mercadolibre.com/categories/{category_id}", headers={
                'Authorization': f'Bearer {self.meli_access_token}'
            })
            category_details_response.raise_for_status()
            category_details = category_details_response.json()
        except requests.RequestException as e:
            self._log(f"Error al obtener detalles para la categoría ID '{category_id}': {str(e)}", level='error')
            return

        # Obtener nombre de la categoría actual y path_from_root
        category_name = category_details.get('name', 'Sin Nombre')
        path_from_root = category_details.get('path_from_root', [])
        complete_name = "/".join([item['name'] for item in path_from_root]) if path_from_root else category_name

        # Determinar si es categoría final
        is_final_category = len(path_from_root) == 3  # Asumiendo que la estructura es Padre/Subpadre/Hijo

        # Obtener el ID de la categoría padre en Odoo, si existe
        parent_id = None
        if len(path_from_root) > 1:
            # Buscar la categoría padre basada en el id de path_from_root
            parent_meli_id = path_from_root[-2]['id']
            parent_category = ProductCategory.search([('meli_category_id', '=', parent_meli_id)], limit=1)
            parent_id = parent_category.id if parent_category else None

        # Buscar o crear la categoría en Odoo
        existing_category = ProductCategory.search([('meli_category_id', '=', category_id)], limit=1)
        if existing_category:
            self._log(f"La categoría '{category_name}' ya existe en Odoo.")
            odoo_category = existing_category
        else:
            odoo_category = ProductCategory.create({
                'name': category_name,
                'meli_category_id': category_id,
                'parent_id': parent_id,
                'complete_name': complete_name,
            })
            self._log(f"Categoría '{category_name} - {category_id}' importada correctamente.")
            return odoo_category.id

        # Procesar subcategorías
        children_categories = category_details.get('children_categories', [])
        for child_category in children_categories:
            child_category_id = child_category.get('id')

            if not child_category_id:
                continue

            # Llamar recursivamente para importar la subcategoría
            # self.import_category_recursive(child_category_id)

        return 
        # codigo final va a hacer lo siguiente: importar todas las categorias del producto(evitando duplicaciones) y regresando el id de la categoria final
    # END CATEGORIES

    # CLIENTS
    def get_client_by_id(self, id: int):
        self.ensure_one()
        self._log(f"Iniciando la importación del cliente con ID {id} desde Mercado Libre")

        url = f"{MERCADO_LIBRE_URL}/users/{id}"
        headers = {
            'Authorization': f'Bearer {self.meli_access_token}'
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            self._log(f"Error al obtener el cliente: {str(e)}", level='error')
            return

        client_data = response.json()
        
        return client_data
    
    def update_client_data_by_id(self, id:int):
        self.ensure_one()
        self._log(f"Iniciando la actualizacion del cliente con ID {id} desde Mercado Libre")
        client_data = self.get_client_by_id(id)

        Partner = self.env['res.partner']

        try:
            client_name = client_data.get('nickname')
            client_city = client_data["address"]["city"]
            client_status = client_data["status"]["site_status"] == "active"
            client_state = client_data["address"]["state"]
            client_country = client_data.get('country_id')

            partner = Partner.search([('name', '=', client_name)], limit=1)
            
            partner.write({
                'name': client_name,
                'active': client_status,
                'city': client_city,
            })
            self._log(f"Cliente {client_name} actualizado correctamente.")
            self._log("Actualización del cliente completada.")
            return partner
        except Exception as ex:
            self._log(f"Error al procesar el cliente {id}: {str(ex)}", level='error')
            raise UserError(f"Error al procesar el cliente {id}: {str(ex)}")
        
    def create_client_by_id(self, id: int):
        self.ensure_one()
        self._log(f"Iniciando la importación del cliente con ID {id} desde Mercado Libre")

        client_data = self.get_client_by_id(id)
        
        Partner = self.env['res.partner']

        try:
            client_name = client_data.get('nickname')
            client_city = client_data["address"]["city"]
            client_status = client_data["status"]["site_status"] == "active"
            client_state = client_data["address"]["state"]
            client_country = client_data.get('country_id')

            partner = Partner.create({
                'name': client_name,
                'active': client_status,
                'city': client_city,
            })
            self._log(f"Cliente {client_name} importado correctamente.")
            self._log("Importación del cliente completada.")
            return partner
        except Exception as ex:
            self._log(f"Error al procesar el cliente {id}: {str(ex)}", level='error')
            raise UserError(f"Error al procesar el cliente {id}: {str(ex)}")
    # END CLIENTS

    # QUESTIONS

    
    
    def format_question(self,question:dict):
        self.ensure_one()
        self._log(f"Iniciando el formateo de la pregunta {question.get('id')}")

        formatted_question = {}
        formatted_question['name'] = f"Pregunta {question.get('id')}"
        formatted_question['meli_item_id'] = question['item_id']
        formatted_question['meli_seller_id'] = question['seller_id']
        formatted_question['meli_status'] = question['status']
        formatted_question['meli_text'] = question['text']
        formatted_question['meli_id'] = question['id']
        formatted_question['meli_deleted_from_listing'] = question['deleted_from_listing']
        formatted_question['meli_hold'] = question['hold']
        formatted_question['meli_answer'] = question.get('answer', {}).get('text') if question.get('answer') else None
        formatted_question['meli_from_id'] = question['from']['id']
        formatted_question['meli_import_type'] = 'product_question'
        formatted_question['meli_created_at'] = datetime.strptime(question['date_created'], '%Y-%m-%dT%H:%M:%S.%f%z').strftime('%Y-%m-%d %H:%M:%S')
        formatted_question['meli_from_nickname'] = question['nickname']
        
        #Si la pregunta ha sido respondida extraemos la hora a la que fue respondida
        if question['answer']:
            self._log("La pregunta ya ha sido respondida guardando fecha")
            formatted_question['meli_answered_at'] = datetime.strptime(question['answer']['date_created'], '%Y-%m-%dT%H:%M:%S.%f%z').strftime('%Y-%m-%d %H:%M:%S')
            self._log(formatted_question)

        self._log(f"Pregunta {question.get('id')} formateada correctamente.")

        return formatted_question
    


    def get_random_name(self):        
        """Genera un nombre al azar."""
        names = ["Pedro", "Juan", "Pablo", "Maria", "Sofia"]
        return random.choice(names)
    
    def get_name_by_id(self,from_id):        

        """Obtiene el nickname desde mercado libre para injectarlo a la pregunta"""
        nombre = "UNKNOWN"

        url = f"{MERCADO_LIBRE_URL}/users/{from_id}"
        headers = {
            'Authorization': f'Bearer {self.meli_access_token}'
        }

        try:    
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            response = response.json()
            nickname = response["nickname"]
            if nickname:
                return nickname
            else:
                return nombre   
                    
        except requests.RequestException as e:
            self._log(f"Error al responder la pregunta: {str(e)}", level='error')
            _logger.info(f"Respuesta de la API: {answered.status_code}")
            _logger.info(f"Contenido de la respuesta: {answered.text}")
            return "error"
        

    def get_questions_by_item_id(self, item_id: str):
        self.ensure_one()
        self._log(f"Iniciando la importación de preguntas para el artículo con ID {item_id} desde Mercado Libre")
        self._log(f"TOKEN1-> {self.meli_access_token}")

        url = f"{MERCADO_LIBRE_URL}/questions/search?item={item_id}"
        headers = {
            'Authorization': f'Bearer {self.meli_access_token}'
        }

        total = 999999
        offset = 0
        limit = 50
        questions = []

        while offset < total:
            try:
                response = requests.get(f"{url}&offset={offset}&limit={limit}", headers=headers)
                response.raise_for_status()
            except requests.RequestException as e:
                self._log(f"Error al obtener preguntas: {str(e)}", level='error')
                return
            self._log(response.text)
            questions_data = response.json()
            questions += questions_data.get('questions', [])
            total = questions_data.get('total', 0)
            limit = questions_data.get('limit', 0)
            offset += limit


        #Agregando logica para agregar nickname a una question 
        # Si se encontraron preguntas, se procesa cada una
        if len(questions) > 0:
            for question in questions:
                # Obtener el id del 'from' de la pregunta, ID del usuario que pregunto
                from_id = question.get('from', {}).get('id')
                if from_id:
                    # Generar un nombre aleatorio y añadirlo a la pregunta
                    nickname = self.get_name_by_id(from_id)
                    question['nickname'] = nickname

                self._log(question)


        self._log(f"Se han encontrado {len(questions)} preguntas para el artículo {item_id}")
        return questions
    
    

    def import_items_questions(self):
        self.ensure_one()
        self._log("Iniciando la importación de preguntas desde Mercado Libre")

        items_ids = self.get_items_ids_by_seller_id(self.perfil_id)

        questions = []
        for item_id in items_ids:
            questions += self.get_questions_by_item_id(item_id)

        formatted_questions = [self.format_question(question) for question in questions]
        fsd = ' - '.join(str(item) for item in formatted_questions)
        #self._log("Finalizacion de formateo")
        #self._log(fsd)
 

        
        Questions = self.env['vex.meli.questions']

        self._log("Finalizacion de env")
        Questions.sudo().multiple_create_if_not_exists(formatted_questions)

        self._log("Importación de preguntas completada.")

    @api.model
    def answer_question(self ,meli_id:str ,response:str,accessToken):
       
        self._log(f"Iniciando la respuesta a la pregunta {meli_id}")

        url = f"{MERCADO_LIBRE_URL}/answers"
        headers = {
            "Authorization": f"Bearer {accessToken}"
        }

        try:
            body = {
                "question_id": meli_id,
                "text": response
            }

            # Agrega logging para depuración
            _logger.info(f"URL de la solicitud: {url}")
            _logger.info(f"Headers de la solicitud: {headers}")
            _logger.info(f"Body de la solicitud: {body}")


            answered = requests.post(url, headers=headers, json=body)
            answered.raise_for_status()
            
            _logger.info(f"Respuesta exitosa")
            _logger.info(f"Respuesta de la API: {answered.status_code}")
            _logger.info(f"Contenido de la respuesta: {answered.text}")

            return True

             

        except requests.RequestException as e:
            self._log(f"Error al responder la pregunta: {str(e)}", level='error')
            # Agrega logging para verificar la respuesta
            _logger.info(f"Respuesta de la API: {answered.status_code}")
            _logger.info(f"Contenido de la respuesta: {answered.text}")
            return False
        self._log(f"Respuesta a la pregunta {meli_id} enviada correctamente.")

    @api.model
    def delete_question(self ,meli_id:str,accessToken):
       
        self._log(f"Iniciando eliminacion de la pregunta{meli_id}")

        url = f"{MERCADO_LIBRE_URL}/questions/{meli_id}"
        headers = {
            "Authorization": f"Bearer {accessToken}"
        }

        try:           
            # Agrega logging para depuración
            _logger.info(f"URL de la solicitud: {url}")
            _logger.info(f"Headers de la solicitud: {headers}")           

            response = requests.delete(url, headers=headers)            
            response.raise_for_status()
            
            _logger.info(f"Respuesta exitosa")
            _logger.info(f"Respuesta de la API: {response.status_code}")

            if response.status_code == 200:
                print("Pregunta eliminada correctamente")
                return True
            else:
                print(f"Error al eliminar la pregunta: {response.status_code}, {response.text}")
                return False                                    

        except requests.RequestException as e:
            self._log(f"Error al eliminar la pregunta: {str(e)}", level='error')
            # Agrega logging para verificar la respuesta
            _logger.info(f"Respuesta de la API: {answered.status_code}")
            _logger.info(f"Contenido de la respuesta: {answered.text}")
            return False
     

    def update_question(self, question_id:str):
        self.ensure_one()
        self._log(f"Iniciando la actualización de la pregunta {question_id} desde Mercado Libre")

        url = f"{MERCADO_LIBRE_URL}/questions/{question_id}"
        headers = {
            'Authorization': f'Bearer {self.meli_access_token}'
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            self._log(f"Error al obtener la pregunta: {str(e)}", level='error')
             # if error == 404 significando que la pregunta no existe, significa que se elimino desde ML
             # Buscar la pregunta en el modelo vex.meli.questions
             
            self._log(f"Se ha recibido una actualizacion de  {question_id} pero no existe en ML significando que es una actualizacion de borrado", level='warning')
            Questions = self.env['vex.meli.questions']
            question = Questions.search([('meli_id', '=', question_id)], limit=1)
            if not question:
                self._log(f"No se encontró la pregunta con ID {question_id}", level='warning')
                return
            try:
                # Eliminar la pregunta encontrada
                question.unlink()
                self._log(f"Pregunta {question_id} eliminada correctamente.")
            except Exception as e:
                self._log(f"Error al eliminar la pregunta {question_id}: {str(e)}", level='error')
                    
            return

        question_data = response.json()
        formatted_question = self.format_question(question_data)
        
        Questions = self.env['vex.meli.questions']
        question = Questions.search([('meli_id', '=', question_id)], limit=1)
        question.write(formatted_question)
        self._log(f"Pregunta {question_id} actualizada correctamente.")

    def create_question(self, question_id:str):
        self.ensure_one()
        self._log(f"Iniciando la importación de la pregunta {question_id} desde Mercado Libre")

        url = f"{MERCADO_LIBRE_URL}/questions/{question_id}"
        headers = {
            'Authorization': f'Bearer {self.meli_access_token}'
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            self._log(f"Error al obtener la pregunta: {str(e)}", level='error')
            return

        question_data = response.json()
        formatted_question = self.format_question(question_data)
        
        Questions = self.env['vex.meli.questions']
        Questions.create(formatted_question)
        self._log(f"Pregunta {question_id} importada correctamente.")

    # END QUESTIONS

    # CHAT
    def format_chat_messages(self, messages:List[dict]):
        self.ensure_one()
        self._log(f"Iniciando el formateo de los mensajes del chat")

        formatted_messages = []

        for message in messages:
            formatted_message = {}
            formatted_message['meli_id'] = message['id']
            formatted_message['meli_site_id'] = message['site_id']
            formatted_message['meli_from_id'] = message.get('from', {}).get('id')
            formatted_message['meli_to_id'] = message.get('to', {}).get('id')
            formatted_message['meli_status'] = message.get('status')
            formatted_message['meli_text'] = message.get('text')

            formatted_messages.append(formatted_message)
        
        self._log(f"Se han formateado {len(formatted_messages)} mensajes del chat correctamente.")
        return formatted_messages

    def get_chat_messages_by_order(self, order_id:int, seller_id:int):
        self.ensure_one()
        self._log(f"Iniciando la importación del chat para la orden con ID {order_id} desde Mercado Libre")
        limit = 1000
        url = f"{MERCADO_LIBRE_URL}/messages/packs/{order_id}/sellers/{seller_id}?tag=post_sale&limit={limit}"
        headers = {
            'Authorization': f'Bearer {self.meli_access_token}'
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            self._log(f"Error al obtener el chat: {str(e)}", level='error')
            return
        
        chat_data = response.json()

        conversation_status = chat_data.get('conversation_status', {}).get('status')
        messages = chat_data.get('messages', [])

        self._log(f"Se han encontrado {len(messages)} mensajes en el chat para la orden {order_id}")

        formatted_messages = self.format_chat_messages(messages)
        return formatted_messages
    
    # END CHAT
    # SHIPMENTS
    def get_shipment(self, shipment_id:int):
        self.ensure_one()
        self._log(f"Iniciando la importación del envío con ID {shipment_id} desde Mercado Libre")

        url = f"{MERCADO_LIBRE_URL}/shipments/{shipment_id}"
        headers = {
            'Authorization': f'Bearer {self.meli_access_token}'
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            self._log(f"Error al obtener el envío: {str(e)}", level='error')
            return
        
        shipment_data = response.json()
        return shipment_data
    # END SHIPMENTS
