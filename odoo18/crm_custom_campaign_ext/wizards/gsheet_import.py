from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
import requests

_logger = logging.getLogger(__name__)

class BcGsheetImportWizard(models.TransientModel):
	_name = 'bc.gsheet.import.wizard'
	_description = 'Importar desde Google Sheets'

	# Campo usado por la vista; ajustar tipo/modelo según tu diseño real
	subcampaign_id = fields.Many2one('bc.subcampaign', string='Subcampaign', readonly=True)

	# Campos requeridos por la vista gsheet_import_views.xml
	sheet_url = fields.Char(string='Sheet URL', placeholder='https://docs.google.com/spreadsheets/d/...', required=True)
	sheet_tab = fields.Char(string='Sheet Tab')
	sheet_range = fields.Char(string='Sheet Range')
	mode = fields.Selection([
		('create', 'Create'),
		('update', 'Update'),
		('create_update', 'Create or Update'),
		('preview', 'Preview'),
	], string='Mode', default='create')

	# Nuevo campo requerido por la vista
	preview_json = fields.Text(string='Preview JSON', readonly=True)

	# ...añadir más campos y métodos según necesidad...

	def _get_n8n_config(self):
		"""Lee la configuración de n8n desde ir.config_parameter.
		No usar URL hardcodeada; si falta la URL informar al usuario."""
		params = self.env['ir.config_parameter'].sudo()
		url = params.get_param('bc.n8n.webhook_url')
		if not url:
			raise UserError('Configura la URL del webhook de n8n en Configuración -> n8n.')
		api_key = params.get_param('bc.n8n.api_key') or False
		# timeout guardado como string; parsear a int con fallback
		try:
			timeout = int(params.get_param('bc.n8n.timeout') or 25)
		except Exception:
			timeout = 25
		# verify_ssl suele almacenarse como 'True'/'False' o '1'/'0'
		verify_val = params.get_param('bc.n8n.verify_ssl')
		verify = True
		if verify_val is not None:
			verify = str(verify_val).lower() in ('1', 'true', 'y', 'yes')
		return {
			'url': url,
			'api_key': api_key,
			'timeout': max(timeout, 5),
			'verify': verify,
		}

	def _post_to_n8n(self, payload):
		"""Envía payload JSON al webhook de n8n usando la configuración guardada."""
		cfg = self._get_n8n_config()
		url = cfg['url']
		headers = {'Content-Type': 'application/json'}
		if cfg['api_key']:
			headers['Authorization'] = f"Bearer {cfg['api_key']}"
		_logger.info('Enviando payload a n8n: %s -> %s', url, payload)
		try:
			resp = requests.post(url, json=payload, headers=headers, timeout=cfg['timeout'], verify=cfg['verify'])
			_logger.info('Respuesta n8n status=%s body=%s', resp.status_code, resp.text)
			resp.raise_for_status()
			return resp
		except Exception as e:
			_logger.exception('Error enviando a n8n: %s', e)
			# Rethrow para que quede en log y en UI si procede.
			raise

	def action_preview(self):
		"""Genera una previsualización mínima y reabre el formulario para mostrar preview_json.
		Reemplazar la generación de preview por la lógica real que lea la hoja."""
		self.ensure_one()
		# Ejemplo simple: crear un JSON de previsualización. Sustituir por lógica real.
		self.preview_json = '{"preview": true, "sheet_url": "%s"}' % (self.sheet_url or "")
		return {
			'type': 'ir.actions.act_window',
			'res_model': self._name,
			'res_id': self.id,
			'view_mode': 'form',
			'target': 'new',
		}

	def action_create(self):
		"""Crear planes y notificar a n8n: envía un POST con los valores del wizard."""
		self.ensure_one()
		# Construir payload con los campos que quieras enviar
		payload = {
			'subcampaign_id': self.subcampaign_id.id if self.subcampaign_id else None,
			'subcampaign_name': self.subcampaign_id.display_name if self.subcampaign_id else None,
			'sheet_url': self.sheet_url,
			'sheet_tab': self.sheet_tab,
			'sheet_range': self.sheet_range,
			'mode': self.mode,
		}
		# Usa configuración desde ir.config_parameter; no hardcodear URL
		self._post_to_n8n(payload)

		# ...real creation logic placeholder...
		# Aquí debes implementar la creación real de 'planes' según tu lógica.
		# Por ahora cerramos el wizard si el POST fue exitoso.
		return {'type': 'ir.actions.act_window_close'}
