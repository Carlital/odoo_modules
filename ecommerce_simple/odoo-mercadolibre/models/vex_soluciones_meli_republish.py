from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import requests

import logging
_logger = logging.getLogger(__name__)

class ProductTemplateInherit(models.Model):
    _inherit         = "product.template"

    @api.model
    def get_products_closed_from_meli(self):
        current_user = self.env.user 
        meli_instance = current_user.meli_instance_id
        
        ACCESS_TOKEN = meli_instance.meli_access_token
        USER_ID = meli_instance.meli_user_id
        items = []
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

        url_get_items = f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=closed"
        res_items = requests.get(url_get_items, headers=headers)

        if res_items.status_code == 200:
            data_response_items = res_items.json()
            for i in data_response_items['results']:
                url_get_data_items = f"https://api.mercadolibre.com/items/{i}"
                res_data = requests.get(url_get_data_items, headers=headers)
                if res_data.status_code == 200:
                    data_response = res_data.json()
                    existing_record = self.search([('meli_id', '=', data_response['id'])], limit=1)
                    if existing_record:
                        existing_record.write({
                            'title': data_response['title'],
                            'image_url': data_response['thumbnail'],
                            'price': data_response['price'],
                            'listing_type': data_response['listing_type_id'],
                            'condition': data_response['condition'],
                            'stop_date': data_response['stop_time'],
                            'quantity': data_response['available_quantity']
                        })
                    else:
                        self.create({
                            'meli_id': data_response['id'],
                            'title': data_response['title'],
                            'image_url': data_response['thumbnail'],
                            'price': data_response['price'],
                            'listing_type': data_response['listing_type_id'],
                            'condition': data_response['condition'],
                            'stop_date': data_response['stop_time'],
                            'quantity': data_response['available_quantity'],
                            'state': 'pending'
                        })
                    print(data_response.get('id'))
                    print("hola")
                    items.append(data_response)
                else:
                    print(f"Error {res_items.status_code}: {res_items.text}")
                    return "Error al obtener datos de la API"
            return items
        else:
            print(f"Error {res_items.status_code}: {res_items.text}")
            return "Error al obtener datos de la API"

    def exec_republish_items(self):
        if not self:
            raise UserError("No has seleccionado ningún producto.")

        registros_invalidos = self.filtered(lambda r: r.meli_status != 'closed')
        if registros_invalidos:
            raise UserError("Solo se puede ejecutar esta acción en publicaciones con estado 'closed'.")

        current_user = self.env.user
        meli_instance = current_user.meli_instance_id

        if not meli_instance or not meli_instance.meli_access_token:
            raise UserError("Tu instancia de MercadoLibre no tiene un token de acceso válido.")

        access_token = meli_instance.meli_access_token
        headers = {"Authorization": f"Bearer {access_token}"}

        for rec in self:
            publication_id = rec.ml_publication_code
            if not publication_id:
                raise UserError(f"El producto {rec.name} no tiene código de publicación.")

            _logger.info("[ML-RELIST] Obteniendo publicación original ID: %s", publication_id)
            get_url = f"https://api.mercadolibre.com/items/{publication_id}"
            get_response = requests.get(get_url, headers=headers)
            original_data = get_response.json()

            if 'error' in original_data:
                raise UserError(f"No se pudo obtener la publicación original: {original_data.get('message')}")

            data_relist = {
                "price": rec.list_price,
                "listing_type_id": rec.listing_type_id,
                "quantity": rec.instance_id.default_quantity_republish,
            }

            # Si tiene variantes, mantener la estructura original
            if 'variations' in original_data and original_data['variations']:
                data_relist['variations'] = []
                for var in original_data['variations']:
                    variation_data = {
                        "attribute_combinations": var.get("attribute_combinations", []),
                        "available_quantity": rec.instance_id.default_quantity_republish,
                        "price": rec.list_price,
                        "picture_ids": var.get("picture_ids", []),
                        "seller_custom_field": var.get("seller_custom_field", ''),
                        "attributes": var.get("attributes", []),
                    }
                    data_relist['variations'].append(variation_data)
                _logger.info("[ML-RELIST] Incluyendo %s variantes para republicación", len(data_relist['variations']))

            url_relist = f"https://api.mercadolibre.com/items/{publication_id}/relist"
            _logger.info("[ML-RELIST] Enviando relist a %s", url_relist)
            post_response = requests.post(url_relist, headers=headers, json=data_relist)
            response_json = post_response.json()

            if 'id' in response_json and response_json.get('status') == "active":
                _logger.info("[ML-RELIST] Publicación %s republicada correctamente con ID %s", publication_id, response_json['id'])

                rec.write({
                    'ml_publication_code': response_json['id'],
                    'default_code': response_json['id'],
                    'meli_status': 'active'
                })

                # Actualizar variantes si aplica
                if 'variations' in response_json:
                    for idx, variant in enumerate(response_json['variations']):
                        if idx < len(rec.product_variant_ids):
                            variant_record = rec.product_variant_ids[idx]
                            variant_record.write({
                                'ml_variation_id': variant.get('id')
                            })
            else:
                _logger.error("[ML-RELIST] Error en republicación: %s", response_json)
                raise UserError(f"Error al republicar: {response_json.get('message', 'Error desconocido')}")

    @api.model
    def cron_republish_items(self):
        current_user = self.env.user 
        meli_instance = current_user.meli_instance_id
        #meli_instance = self.env['vex.instance'].search([('name', '=', 'Tienda test dos')])
        if meli_instance.auto_republish:
            items_closed = self.search([('meli_status', '=', 'closed')])
            if items_closed:
                items_closed.exec_republish_items()
        
class VexInstanceInherit(models.Model):
    _inherit         = "vex.instance"


    auto_republish = fields.Boolean('auto_republish')
    default_quantity_republish = fields.Integer('default_quantity_republish')
