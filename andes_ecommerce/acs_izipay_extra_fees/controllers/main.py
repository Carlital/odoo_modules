from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class IzipayExtraFeesController(http.Controller):

    @http.route('/acs_izipay_extra_fees/get_surcharge_info', type='json', auth='public', methods=['POST'])
    def get_surcharge_info(self):
        """
        Obtiner el porcentaje de recargo y el producto de recargo basado por ID del proveedor
        """
        json_data = request.httprequest.get_json(silent=True)
        provider_id = json_data.get('provider_id') if json_data else None

        if not provider_id:
            _logger.error("No se proporcionó un ID de proveedor.")
            return {'result': {'surcharge_percentage': 0, 'surcharge_product_id': None}}

        provider = request.env['payment.provider'].sudo().search([('id', '=', provider_id)], limit=1)
        
        if not provider:
            _logger.error("No se encontró el proveedor con ID: %s", provider_id)
            return {'result': {'surcharge_percentage': 0, 'surcharge_product_id': None}}

        surcharge_percentage = provider.surcharge_percentage or 0
        surcharge_product_id = provider.surcharge_product_id.id if provider.surcharge_product_id else None
        surcharge_product_name = provider.surcharge_product_id.name if provider.surcharge_product_id else "Recargo"

        response = {
            'result': {
                'surcharge_percentage': surcharge_percentage,
                'surcharge_product_id': surcharge_product_id,
                'surcharge_product_name': surcharge_product_name
            }
        }

        return response

    @http.route('/acs_izipay_extra_fees/apply_surcharge', type='json', auth='public', methods=['POST'])
    def apply_surcharge(self):
        """
        Aplica recargo a la orden en el backend.
        """
        json_data = request.httprequest.get_json(silent=True)
        order_id = json_data.get('order_id')
        surcharge_product_id = json_data.get('surcharge_product_id')
        surcharge_amount = json_data.get('surcharge_amount')

        if not order_id or not surcharge_product_id or surcharge_amount <= 0:
            _logger.error("Datos incompletos o incorrectos para aplicar el recargo.")
            return {'error': 'No se pudo aplicar el recargo. Información incompleta o incorrecta.'}

        order = request.env['sale.order'].sudo().browse(order_id)
        if order:
            order._apply_surcharge_dynamic(surcharge_product_id, surcharge_amount)
            return {'success': True}

        return {'error': 'Orden no encontrada.'}
    
