from odoo import api, fields, models, _
from odoo.exceptions import UserError
import json
import logging

_logger = logging.getLogger(__name__)


class N8nConfig(models.TransientModel):
    _name = 'bc.n8n.config'
    _description = 'Configuración de n8n (vista de sistema)'
    _inherit = 'res.config.settings'

    n8n_webhook_url = fields.Char(string='n8n Webhook URL', config_parameter='bc.n8n.webhook_url')
    n8n_api_key = fields.Char(string='n8n API Key', config_parameter='bc.n8n.api_key')
    n8n_timeout = fields.Integer(string='Timeout (s)', default=25, config_parameter='bc.n8n.timeout')
    n8n_verify_ssl = fields.Boolean(string='Verificar SSL', default=True, config_parameter='bc.n8n.verify_ssl')

    n8n_last_check_ok = fields.Boolean(string='Última prueba OK', readonly=True)
    n8n_last_check_at = fields.Datetime(string='Probado el', readonly=True)
    n8n_last_error = fields.Text(string='Último error', readonly=True)

    def action_test_connection(self):
        self.ensure_one()
        url = self.n8n_webhook_url
        if not url:
            raise UserError(_('Configura el Webhook URL de n8n.'))

        headers = {'Content-Type': 'application/json'}
        if self.n8n_api_key:
            headers['Authorization'] = f"Bearer {self.n8n_api_key}"

        # Enviar como params en GET para la prueba
        params = {
            'action': 'ping',
            'source': 'odoo',
            'module': 'crm_custom_campaign_ext',
        }

        timeout = max(self.n8n_timeout or 25, 5)
        verify = bool(self.n8n_verify_ssl)

        try:
            import requests
            # Usar GET para la comprobación de conectividad
            resp = requests.get(url, params=params, headers=headers, timeout=timeout, verify=verify)
            ok = resp.status_code // 100 == 2
            data = {}
            try:
                data = resp.json()
            except Exception:
                pass

            # Detectar caso típico de n8n: webhook no registrado / workflow no ejecutado
            if resp.status_code == 404:
                # intentar extraer mensaje de la respuesta JSON si existe
                resp_message = ''
                if isinstance(data, dict):
                    resp_message = data.get('message') or data.get('error') or data.get('status') or ''
                else:
                    resp_message = resp.text or ''
                # Mensaje conocido enviado por n8n cuando el webhook no está activo
                if 'not registered' in resp_message or 'Execute workflow' in resp_message or 'webhook' in resp_message and 'not registered' in resp_message.lower():
                    display = _(
                        "El webhook no está registrado en n8n o el workflow no está 'Execute'. "
                        "Abre tu workflow en n8n y pulsa 'Execute workflow' (en modo test solo acepta una llamada)."
                    )
                    self.write({
                        'n8n_last_check_ok': False,
                        'n8n_last_check_at': fields.Datetime.now(),
                        'n8n_last_error': resp_message or display,
                    })
                    raise UserError(display)
                # si es 404 genérico, intentar GET al host base para comprobar conectividad
                try:
                    from urllib.parse import urlsplit
                    parts = urlsplit(url)
                    base = f"{parts.scheme}://{parts.netloc}" if parts.scheme and parts.netloc else url
                    conn_resp = requests.get(base, timeout=5, verify=verify)
                    host_ok = conn_resp.status_code // 100 == 2
                except Exception as e_conn:
                    host_ok = False
                    _logger.debug('Fallback host check failed: %s', e_conn)
                if host_ok:
                    message = _('Host accesible pero webhook no encontrado (404). Verifica el path y activa el workflow en n8n.')
                else:
                    message = _('No se pudo conectar al host de n8n. Revisa red/firewall/proxy.')
                self.write({
                    'n8n_last_check_ok': False,
                    'n8n_last_check_at': fields.Datetime.now(),
                    'n8n_last_error': message,
                })
                raise UserError(message)

            # Si no fue 2xx y no fue manejado arriba, usar el texto/JSON
            message = data.get('status') if isinstance(data, dict) else resp.text
            self.write({
                'n8n_last_check_ok': ok,
                'n8n_last_check_at': fields.Datetime.now(),
                'n8n_last_error': '' if ok else (message or f'Status {resp.status_code}')
            })
            if not ok:
                raise UserError(_('Conexión fallida: %s') % (self.n8n_last_error or ''))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Conexión exitosa'),
                    'message': _('n8n respondió correctamente (GET).'),
                    'type': 'success',
                }
            }
        except UserError:
            # Re-lanzar UserError tal cual para que llegue a la UI
            raise
        except Exception as e:
            _logger.exception('Error probando conexión n8n (GET)')
            self.write({
                'n8n_last_check_ok': False,
                'n8n_last_check_at': fields.Datetime.now(),
                'n8n_last_error': str(e),
            })
            raise UserError(_('Error conectando con n8n: %s') % e)


def post_init_hook(cr, registry):
    """Create a CRM -> Configuration -> n8n menu if a suitable parent exists.
    More robust lookup: try known xmlids, then search by menu name (localized),
    finally try to attach under a campaign-related menu by name.
    """
    from odoo import api, SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})
    md = env['ir.model.data']
    Menu = env['ir.ui.menu']

    # Candidate parent xmlids (order = preferred)
    parent_xids = [
        'crm.menu_config',
        'crm.menu_crm_root',
        'crm_custom_lead.menu_crm_custom_campaign_root',
    ]

    parent_id = None
    for xid in parent_xids:
        try:
            model, res_id = md._xmlid_to_res_model_res_id(xid, raise_if_not_found=True)
            if model == 'ir.ui.menu':
                parent_id = res_id
                break
        except Exception:
            continue

    # If xmlid search failed, try to find an existing "Configuration"/"Configuración" menu
    if not parent_id:
        conf_menu = Menu.search([('name', 'in', ['Configuration', 'Configuración'])], limit=1)
        if conf_menu:
            parent_id = conf_menu.id

    # If still not found, try to find a visible campaign-related menu and attach there
    if not parent_id:
        campaign_menu = Menu.search([('name', 'ilike', 'campan')], limit=1)
        if not campaign_menu:
            campaign_menu = Menu.search([('name', 'ilike', 'campaign')], limit=1)
        if campaign_menu:
            conf_child = Menu.search([('parent_id', '=', campaign_menu.id), ('name', 'in', ['Configuración', 'Configuration'])], limit=1)
            if conf_child:
                parent_id = conf_child.id
            else:
                root = Menu.create({
                    'name': 'Configuración',
                    'parent_id': campaign_menu.id,
                    'sequence': 95,
                })
                md.create({
                    'module': 'crm_custom_campaign_ext',
                    'name': 'menu_bc_root_config',
                    'model': 'ir.ui.menu',
                    'res_id': root.id,
                })
                parent_id = root.id

    if not parent_id:
        return

    try:
        md._xmlid_to_res_model_res_id('crm_custom_campaign_ext.menu_bc_n8n_config', raise_if_not_found=True)
        return
    except Exception:
        pass

    try:
        action = env.ref('crm_custom_campaign_ext.action_bc_n8n_config', raise_if_not_found=False)
        child_vals = {
            'name': 'n8n',
            'parent_id': parent_id,
            'sequence': 10,
        }
        if action:
            child_vals['action'] = action.id
        child = Menu.create(child_vals)
        md.create({
            'module': 'crm_custom_campaign_ext',
            'name': 'menu_bc_n8n_config',
            'model': 'ir.ui.menu',
            'res_id': child.id,
        })
    except Exception as e:
        _logger.exception('Error creando menú n8n en post_init_hook: %s', e)

