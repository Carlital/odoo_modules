from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class N8nConfigWizard(models.TransientModel):
    _name = 'bc.n8n.config.wizard'
    _description = 'Wizard modal para configurar n8n (popup)'

    n8n_webhook_url = fields.Char(string='n8n Webhook URL')
    n8n_timeout = fields.Integer(string='Timeout (s)', default=25)
    n8n_verify_ssl = fields.Boolean(string='Verificar SSL', default=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        icp = self.env['ir.config_parameter'].sudo()
        url = icp.get_param('bc.n8n.webhook_url')
        timeout = icp.get_param('bc.n8n.timeout')
        verify = icp.get_param('bc.n8n.verify_ssl')
        if url is not None:
            res.setdefault('n8n_webhook_url', url)
        if timeout is not None:
            try:
                res.setdefault('n8n_timeout', int(timeout))
            except Exception:
                res.setdefault('n8n_timeout', 25)
        if verify is not None:
            res.setdefault('n8n_verify_ssl', verify in ('True', '1', True))
        return res

    def action_test(self):
        self.ensure_one()
        url = self.n8n_webhook_url
        if not url:
            raise UserError(_('Configura el Webhook URL de n8n.'))
        payload = {'action': 'ping'}
        headers = {'Content-Type': 'application/json'}
        timeout = max(self.n8n_timeout or 25, 5)
        verify = bool(self.n8n_verify_ssl)
        try:
            import requests
            resp = requests.post(url, json=payload, headers=headers, timeout=timeout, verify=verify)
            ok = resp.status_code // 100 == 2
            msg = ''
            try:
                data = resp.json()
                if isinstance(data, dict):
                    msg = data.get('status') or str(data)
                else:
                    msg = str(data)
            except Exception:
                msg = resp.text or f'Status {resp.status_code}'
            if ok:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Conexión exitosa'),
                        'message': _('n8n respondió correctamente.'),
                        'type': 'success',
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Conexión fallida'),
                        'message': msg or _('Estado %s') % resp.status_code,
                        'type': 'danger',
                    }
                }
        except Exception as e:
            _logger.exception('Error probando conexión n8n (wizard)')
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error de conexión'),
                    'message': str(e),
                    'type': 'danger',
                }
            }

    def action_save(self):
        self.ensure_one()
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param('bc.n8n.webhook_url', self.n8n_webhook_url or '')
        icp.set_param('bc.n8n.timeout', str(self.n8n_timeout or 25))
        icp.set_param('bc.n8n.verify_ssl', '1' if self.n8n_verify_ssl else '0')
        return {'type': 'ir.actions.act_window_close'}

