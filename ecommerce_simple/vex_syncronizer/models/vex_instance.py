from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
import json
import requests
# Configura el logger
_logger = logging.getLogger(__name__)

class VexInstace(models.Model):
    _name = 'vex.instance'
    _rec_name = 'name'
    _description = 'Vex Instance'

    name = fields.Char('Name', required=True)

    status = fields.Selection([
        ('introduction', 'INTRODUCTION'),
        ('initial_settings', 'INITIAL SETTINGS'),
        ('keys', 'KEYS'),
        ('settings', 'SETTINGS')
    ], string='Status', default="introduction")
    image = fields.Image('Image') # , max_width=30, max_height=30
    url_license = fields.Char(default='https://www.pasarelasdepagos.com/')
    license_secret_key = fields.Char(default='587423b988e403.69821411')
    license_key = fields.Char(string='Licence Key', help='Licence Key by Pasarela de pagos', default='')
    license_valid_str = fields.Char(string="License Status", store=True, readonly=True)
    license_valid = fields.Selection([
        ('activo', 'Active'),
        ('inactivo', 'Inactive')
    ], string="License Status")

    license_date_created = fields.Char(string='Licence Date Created', default='', readonly=True)
    license_renewed = fields.Char(string='Licence Date Renovad', default='', readonly=True)
    license_expiry = fields.Char(string='Licence Date Expiry', default='', readonly=True)
    license_message = fields.Char(string='Licence Message', default='', readonly=True)
    store_type = fields.Selection([
    ], string="Store Type", required=True)
    registered_domain = fields.Char('Registered domain', default=lambda self: self.env['ir.config_parameter'].sudo().get_param('web.base.url'))

    state_filter = fields.Selection([
        ('all', 'All'),
        ('error', 'Error'),
        ('obs', 'Observation'),
        ('done', 'Done'),
        ('pending', 'Pending'),
    ], string="Filter by Status", default='all')
    filtered_import_line_ids = fields.One2many('vex.import_line', string="Filtered Import Lines", compute="_compute_filtered_lines", store=False)
    import_line_ids = fields.One2many('vex.import_line', 'instance_id', string='import_line')
    sync_queue_ids = fields.One2many('vex.sync.queue', 'instance_id', string='Sync Queue')
    
    def register_licence(self):
        for provider in self:
            if provider.license_key:
                domain = self.env['ir.config_parameter'].sudo().get_param('web.base.url')\
                    .replace('http://', '').replace('https://', '')

                key = provider.license_key
                secret = provider.license_secret_key #'587423b988e403.69821411'
                reference = provider.store_type

                urls = {
                    'activate': f"https://www.pasarelasdepagos.com/?slm_action=slm_activate&license_key={key}"
                                f"&registered_domain={domain}&secret_key={secret}&item_reference={reference}_odoo",
                    'check': f"https://www.pasarelasdepagos.com/?slm_action=slm_check&license_key={key}"
                            f"&secret_key={secret}",
                }

                headers = {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }

                self._log([domain, urls['activate'], urls['check'], json.dumps(headers)], 'info')

                def update_from_check():
                    try:
                        check_response = requests.get(urls['check'], headers=headers, timeout=15)
                        if check_response.status_code == 200:
                            data = check_response.json()
                            if data.get('result') == 'success':
                                provider.license_valid_str = 'active'
                                provider.license_date_created = data.get('date_created')
                                provider.license_renewed = data.get('date_renewed')
                                provider.license_expiry = data.get('date_expiry')
                                full_name = f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
                                company = data.get('company_name', '')
                                expiry = data.get('date_expiry', '')
                                message = ""

                                if data.get('status') == "active":
                                    message = "The license is active"
                                    msg = f"Licencia válida. Nombre: {full_name}, Empresa: {company}, Fecha de Expiración: {expiry}"
                                    self._log(f"CHECK - {msg}", 'info')
                                elif data.get('status') == "expired":
                                    message = "The license has expired"
                                    msg = f"Licencia inválida. Nombre: {full_name}, Empresa: {company}, Fecha de Expiración: {expiry}"
                                    self._log(f"CHECK - {msg}", 'info')

                                provider.license_message = message

                                return self._notify_user('Validation Result', message, 'info', reload=True)
                            else:
                                return self._notify_user('Check Error', data.get('message', 'Error en verificación.'), 'danger', reload=True)
                        else:
                            return self._notify_user('Check Error', f'HTTP Error {check_response.status_code}', 'danger', reload=True)
                    except Exception as e:
                        _logger.exception("Exception during check after activation")
                        return self._notify_user('Check Error', str(e), 'danger', reload=True)

                try:
                    response = requests.get(urls['activate'], headers=headers, timeout=15)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('result') == 'success':
                            # Llamar a check si la activación fue exitosa
                            return update_from_check()
                        else:
                            return self._notify_user(
                                'Activation Error',
                                data.get('message', 'Error desconocido al activar la licencia.'),
                                'danger',
                                reload=True
                            )
                    else:
                        return self._notify_user('Activation Error', f'HTTP Error {response.status_code}', 'danger', reload=True)
                except Exception as e:
                    _logger.exception("Exception during licence activation")
                    return self._notify_user('Activation Error', str(e), 'danger', reload=True)

        return self._notify_user('Validation Error', 'Debe ingresar una clave de licencia válida.', 'danger')

    def check_licence(self):
        for provider in self:
            if provider.license_key:
                domain = self.env['ir.config_parameter'].sudo().get_param('web.base.url')\
                    .replace('http://', '').replace('https://', '')

                key = provider.license_key
                secret = provider.license_secret_key

                url = f"https://www.pasarelasdepagos.com/?slm_action=slm_check&license_key={key}&secret_key={secret}"

                headers = {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }

                self._log([domain, url, json.dumps(headers)], 'info')

                try:
                    response = requests.get(url, headers=headers, timeout=15)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('result') == 'success':
                            return True
                        else:
                            _logger.warning(f"Check licence failed: {data.get('message')}")
                            return False
                    else:
                        _logger.error(f"HTTP error during licence check: {response.status_code}")
                        return False
                except Exception as e:
                    _logger.exception(f"Exception during licence check: {e}")
                    return False

        return False

    def _log(self, message, level='info'):
        if isinstance(message, list):
            message = ' - '.join(message)
        log_method = getattr(_logger, level, _logger.info)
        log_method(message)
        try:
            print(message)
        except UnicodeEncodeError:
            print(message.encode('utf-8', errors='replace').decode('utf-8'))
    
    def _notify_user(self, title, message, message_type='info', reload=False):
        params = {
            'title': _(title),
            'message': _(message),
            'type': message_type,
            'sticky': False
        }

        if reload:
            params['next'] = {
                'type': 'ir.actions.client',
                'tag': 'reload'
            }

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': params
        }
        
    def test_connection(self):
        self.check_licence()

    def stop_sync(self):
        # cron = self.env['ir.cron'].search([('argument', '=', 'vex_cron'),"|",("active", "=", True), ("active", "=", False)])
        # if cron:
        #     cron.active = False
        pass

    def start_sync(self):
        # print("start_sync")
        self.env['vex.synchro'].sync_import()        

    @api.depends('state_filter', 'import_line_ids.status')
    def _compute_filtered_lines(self):
        for rec in self:
            if rec.state_filter == 'all':
                rec.filtered_import_line_ids = rec.import_line_ids
            else:
                rec.filtered_import_line_ids = rec.import_line_ids.filtered(
                    lambda l: l.status == rec.state_filter
                )
    
    def action_start_sync(self):
        pass