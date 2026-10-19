from odoo import models, api, fields
from odoo.exceptions import UserError
import requests
import json
import logging

_logger = logging.getLogger(__name__)

class VexSyncQueueInherit(models.Model):
    _inherit = 'vex.sync.queue'

    @api.model
    def process_meli_sync_queue(self):
        """Procesa 20 productos del queue con estado 'pending' y acción 'product'."""
        domain = [('status', 'in', ['pending','error']), ('action', '=', 'product')]
        queue_lines = self.env['vex.sync.queue'].search(domain, limit=20)

        # Buscar el marketplace con XML ID
        xml_marketplace = self.env.ref('odoo-mercadolibre.vex_marketplace_mercadolibre', raise_if_not_found=False)
        if not xml_marketplace:
            _logger.warning("⚠️ No se encontró el registro 'vex_marketplace_mercadolibre'. Verifica tus datos de instalación.")

        Product = self.env['product.template']

        for line in queue_lines:
            try:
                if not line.description:
                    line.write({'status': 'error', 'result': 'Falta descripción'})
                    continue
                _logger.info(f"Procesando producto: {line.description}")
                instance = line.instance_id
                instance.get_access_token()
                access_token = instance.meli_access_token
                if not access_token:
                    raise UserError("No se ha definido el token de acceso en la instancia vinculada.")

                url = f"https://api.mercadolibre.com/items/{line.description}?include_attributes=all"
                headers = {'Authorization': f'Bearer {access_token}'}
                response = requests.get(url, headers=headers)

                if response.status_code != 200:
                    line.write({
                        'status': 'error',
                        'result': f"API ML {response.status_code} - {response.text}",
                        'start_date': fields.Datetime.now(),
                        'end_date': fields.Datetime.now(),
                    })
                    continue

                data = response.json()
                meli_id = data.get('id')
                if not meli_id:
                    line.write({'status': 'error', 'result': 'ID de producto no encontrado en JSON', 'start_date': fields.Datetime.now(), 'end_date': fields.Datetime.now()})
                    continue

                product = Product.search([('meli_product_id', '=', meli_id)], limit=1)
                vals = {
                    'name': data.get('title', 'Sin título'),
                    'meli_product_id': meli_id,
                    'detailed_type': 'product',
                    'instance_id': instance.id,
                    'meli_json_data': json.dumps(data),
                }
                # Obtener la categoría de MercadoLibre
                meli_category_id = data.get('category_id')
                if not meli_category_id:
                    line.write({'status': 'error', 'result': 'No se encontró category_id en el producto', 'start_date': fields.Datetime.now(), 'end_date': fields.Datetime.now()})  
                    continue

                Category = self.env['product.category']
                category = Category.search([('meli_category_id', '=', meli_category_id)], limit=1)

                if not category:
                    # Consultar la API de MercadoLibre para obtener los datos de la categoría
                    cat_url = f"https://api.mercadolibre.com/categories/{meli_category_id}"
                    cat_response = requests.get(cat_url, headers=headers)
                    if cat_response.status_code == 200:
                        cat_data = cat_response.json()
                        category = Category.create({
                            'name': cat_data.get('name', meli_category_id),
                            'meli_category_id': meli_category_id,
                            'instance_id': instance.id,
                            'parent_id': 1,  # Asignar el padre si es necesario
                            'marketplace_ids': [(4, xml_marketplace.id)] 
                        })
                    else:
                        line.write({'status': 'error', 'result': f"No se pudo obtener la categoría ML {meli_category_id}: {cat_response.text}", 'start_date': fields.Datetime.now(), 'end_date': fields.Datetime.now()})
                        continue

                vals['categ_id'] = category.id

                if xml_marketplace:
                    vals['marketplace_ids'] = [(4, xml_marketplace.id)]

                if product:
                    product.write(vals)
                    product.action_get_details()
                    product.set_image_from_meli()
                    line.write({
                        'status': 'done',
                        'result': f'Producto actualizado: {meli_id}',
                        'start_date': fields.Datetime.now(),
                        'end_date': fields.Datetime.now(),
                    })
                else:
                    new_product = Product.create(vals)
                    new_product.action_get_details()
                    new_product.set_image_from_meli()
                    line.write({
                        'status': 'done',
                        'result': f'Producto creado: {meli_id}',
                        'start_date': fields.Datetime.now(),
                        'end_date': fields.Datetime.now(),
                    })


            except Exception as e:
                _logger.error(f"❌ Error procesando producto {line.description}: {str(e)}")
                line.write({'status': 'error', 'result': str(e), 'start_date': fields.Datetime.now(), 'end_date': fields.Datetime.now()})

    
    def process_meli_order_queue(self):
        """Procesa 20 órdenes del queue con estado 'pending' y acción 'order'."""
        domain = [('status', 'in', ['pending','error']), ('action', '=', 'order')]
        queue_lines = self.env['vex.sync.queue'].search(domain, limit=20)

        for line in queue_lines:
            try:
                if not line.description:
                    line.write({'status': 'error', 'result': 'Falta descripción'})
                    continue
                _logger.info(f"Procesando orden: {line.description}")
                meli_partner_id = self.env.ref('odoo-mercadolibre.res_partner_cliente_meli').id
                instance = line.instance_id
                instance.get_access_token()
                meli_order_id = line.description
                if not meli_order_id:
                    line.write({'status': 'error', 'result': 'ID de orden no encontrado en JSON', 'start_date': fields.Datetime.now(), 'end_date': fields.Datetime.now()})
                    continue

                # Aquí puedes agregar la lógica para procesar la orden
                sale_order = self.env['sale.order'].search([('meli_order_id', '=', meli_order_id)], limit=1)
                if sale_order:
                    sale_order.action_get_details()  # Actualizar detalles de la orden si es necesario
                else:
                    # Crear una nueva orden de venta
                    sale_order = self.env['sale.order'].create({
                        'meli_order_id': meli_order_id,
                        'instance_id': instance.id,
                        'marketplace_ids': [(4, self.env.ref('odoo-mercadolibre.vex_marketplace_mercadolibre').id)],
                        'partner_id': meli_partner_id,  # Asignar el cliente
                        # Agregar más campos según sea necesario
                    })
                    sale_order.action_get_details()
                    sale_order.action_get_shipping_details()
                    sale_order.action_get_customer_details()
                    sale_order.action_copy_datetime_to_date()
                # Por ejemplo, crear un registro de venta o actualizar uno existente

                line.write({
                    'status': 'done',
                    'result': f'Orden procesada: {meli_order_id}',
                    'start_date': fields.Datetime.now(),
                    'end_date': fields.Datetime.now(),
                })

            except Exception as e:
                _logger.error(f"❌ Error procesando orden {line.description}: {str(e)}")
                line.write({'status': 'error', 'result': str(e), 'start_date': fields.Datetime.now(), 'end_date': fields.Datetime.now()})