# -*- coding: utf-8 -*-

import json
from odoo import http
from odoo.http import request


class Api(http.Controller):

    @http.route('/api/stock', type='http', auth='public', methods=['GET'], csrf=True)
    def api_stock(self, **kwargs):
        data = {}
        domain = []
        if kwargs.get('sku'):
            domain.append(('default_code', '=', kwargs['sku']))
        product_ids = request.env['product.product'].sudo().search(domain)
        if not product_ids and kwargs.get('sku'):
            data['Error'] = 'No se encontro ningun producto con el sku {0}'.format(kwargs['sku'])
            return json.dumps(data, indent=4)
        products_qty = product_ids.with_context(location=15).sudo()._compute_quantities_dict(False, False, False)
        if kwargs.get('sku'):
            for id in products_qty:
                data[request.env['product.product'].sudo().browse(id).name] = products_qty[id]['qty_available']
        else:
            for id in products_qty:
                if products_qty[id]['qty_available']:
                    data[request.env['product.product'].sudo().browse(id).name] = products_qty[id]['qty_available']
        return json.dumps(data, indent=4)
