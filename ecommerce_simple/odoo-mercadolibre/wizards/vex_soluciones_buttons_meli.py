from odoo import models, fields, api
from odoo.exceptions import UserError
import json
import requests
import logging
import base64

_logger = logging.getLogger(__name__)

class ProductMeliUpdateStock(models.TransientModel):
    _name = 'product.meli.update.stock'
    _description = 'Sincronizar Stock MercadoLibre'

    product_id = fields.Many2one('product.template', string='Producto', readonly=True)
    current_qty = fields.Float(string='Stock actual', readonly=True)
    new_qty = fields.Float(string='Nuevo stock')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        product = self.env['product.template'].browse(self.env.context.get('default_product_id'))
        res.update({
            'product_id': product.id,
            'current_qty': product.meli_available_quantity or product.qty_available,
            'new_qty': product.meli_available_quantity or product.qty_available,
        })
        return res

    def _create_or_update_stock(self, product_id, stock_qty, stock_location_id, debug=False):
        """
        Crea o actualiza el stock de un producto en una ubicación específica usando su ID.

        :param product_id: ID del producto (product.template).
        :param stock_qty: Cantidad de stock a establecer.
        :param stock_location_id: ID de la ubicación (stock.location).
        :param debug: Si es True, activa los logs para esta función.
        """
        
        log = _logger.info if debug else lambda *args, **kwargs: None

        log("Iniciando proceso para actualizar/crear stock para el producto ID: %s en la ubicación ID: %s", product_id, stock_location_id)

        StockQuant = self.env['stock.quant']
        StockLocation = self.env['stock.location']
        Product = self.env['product.product']

        # Verificar si el producto existe
        product = Product.search([('product_tmpl_id', '=', product_id)], limit=1)
        if not product.exists():
            _logger.error("No se encontró un producto con el ID: %s", product_id)
            raise ValueError(f"No se encontró un producto con el ID: {product_id}")

        log("Producto encontrado: %s (ID: %s)", product.name, product.id)

        # Verificar si la ubicación existe
        location = StockLocation.browse(stock_location_id)
        if not location.exists():
            _logger.error("No se encontró la ubicación con ID: %s", stock_location_id)
            raise ValueError(f"No se encontró la ubicación con ID: {stock_location_id}")

        log("Ubicación seleccionada: %s (ID: %s)", location.complete_name, location.id)

        # Buscar el stock.quant para el producto y la ubicación
        quant = StockQuant.search([
            ('product_id', '=', product.id),
            ('location_id', '=', location.id)
        ], limit=1)

        if quant:
            log("Se encontró un stock.quant existente. Actualizando cantidad de %s a %s", quant.quantity, stock_qty)
            quant.quantity = stock_qty
        else:
            log("No se encontró un stock.quant para el producto %s en la ubicación %s. Creando uno nuevo.", product.name, location.complete_name)
            StockQuant.create({
                'product_id': product.id,
                'location_id': location.id,
                'quantity': stock_qty,
                'inventory_quantity': stock_qty,
            })
            log("Nuevo stock.quant creado para el producto %s con cantidad %s en la ubicación %s.", product.name, stock_qty, location.complete_name)

        log("Proceso de actualización/creación de stock completado con éxito.")

    def action_confirm(self):
        self.ensure_one()
        product = self.product_id

        _logger.info("[ML-STOCK] Iniciando actualización de stock para el producto: %s (ID: %s)", product.name, product.id)

        # Determinar ubicación según logística de ML
        if product.meli_logistic_type != 'fulfillment':
            location = self.env.ref('odoo-mercadolibre.stock_location_ml_not_full')
        else:
            location = self.env.ref('odoo-mercadolibre.stock_location_ml_full')

        location_id = location.id
        self._create_or_update_stock(product.id, self.new_qty, location_id)

        _logger.info("[ML-STOCK] Stock actualizado correctamente en Odoo.")

        # Verificar datos de publicación en ML
        if not product.meli_product_id:
            _logger.error("[ML-STOCK] El producto no tiene código de publicación.")
            raise UserError("Este producto no tiene código de publicación en MercadoLibre.")

        instance = product.instance_id
        if not instance or not instance.meli_access_token:
            _logger.error("[ML-STOCK] Instancia o token de acceso no definido para el producto.")
            raise UserError("No se ha definido la instancia de MercadoLibre o el token de acceso.")

        # Obtener token actualizado
        instance.get_access_token()
        access_token = instance.meli_access_token
        _logger.info("[ML-STOCK] Token obtenido correctamente para la instancia '%s'", instance.name)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        try:
            _logger.info("[ML-STOCK] Consultando publicación en ML para ID: %s", product.meli_product_id)
            item_response = requests.get(
                f"https://api.mercadolibre.com/items/{product.meli_product_id}",
                headers=headers
            )
            item_data = item_response.json()

            if 'error' in item_data:
                _logger.error("[ML-STOCK] Error al obtener publicación: %s", item_data.get('message'))
                raise UserError(f"Error consultando publicación: {item_data.get('message')}")

            new_qty = int(self.new_qty)

            # Actualizar stock en ML (con o sin variantes)
            if 'variations' in item_data and item_data['variations']:
                variation_id = item_data['variations'][0]['id']
                url = f"https://api.mercadolibre.com/items/{product.meli_product_id}/variations/{variation_id}"
                payload = {"available_quantity": new_qty}
                _logger.info("[ML-STOCK] Publicación con variantes. Actualizando variation_id %s con cantidad: %s", variation_id, new_qty)
            else:
                url = f"https://api.mercadolibre.com/items/{product.meli_product_id}"
                payload = {"available_quantity": new_qty}
                _logger.info("[ML-STOCK] Publicación sin variantes. Actualizando cantidad a: %s", new_qty)

            _logger.info("[ML-STOCK] Enviando PUT a %s con payload: %s", url, payload)
            response = requests.put(url, headers=headers, data=json.dumps(payload))

            if response.status_code != 200:
                _logger.error("[ML-STOCK] Error en respuesta PUT: %s", response.text)
                raise UserError(f"Error al actualizar stock: {response.status_code} - {response.text}")

            _logger.info("[ML-STOCK] Stock actualizado correctamente en MercadoLibre.")
            product.action_get_details()

        except Exception as e:
            _logger.exception("[ML-STOCK] Excepción inesperada durante la actualización.")
            raise UserError(f"Ocurrió un error inesperado al enviar el stock a MercadoLibre:\n{str(e)}")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Stock Actualizado',
                'message': 'El stock fue actualizado correctamente en Odoo y en MercadoLibre.',
                'type': 'success',
                'sticky': False,
                "next": {"type": "ir.actions.act_window_close"},
            }
        }



class UpdateMeliPriceWizard(models.TransientModel):
    _name = 'update.meli.price.wizard'
    _description = 'Actualizar Precio en MercadoLibre'

    product_id = fields.Many2one('product.template', string="Producto", required=True, readonly=True)
    current_price = fields.Float(string="Precio Actual", readonly=True)
    new_price = fields.Float(string="Nuevo Precio", required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        product = self.env['product.template'].browse(self.env.context.get('active_id'))
        res.update({
            'product_id': product.id,
            'current_price': product.meli_price or product.list_price,
            'new_price': product.meli_price or product.list_price,
        })
        return res

    def action_update_price(self):
        self.ensure_one()
        product = self.product_id
        publication_id = product.meli_product_id

        _logger.info("[ML-PRICE] Iniciando actualización de precio para producto: %s (ID: %s)", product.name, product.id)

        if not publication_id:
            _logger.error("[ML-PRICE] No se encontró código de publicación.")
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Error",
                    "message": "El producto no tiene un código de publicación en MercadoLibre.",
                    "type": "danger",
                    "sticky": True,
                }
            }

        instance = product.instance_id
        instance.get_access_token()
        access_token = instance.meli_access_token

        if not access_token:
            _logger.error("[ML-PRICE] Token inválido o no disponible.")
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Error",
                    "message": "No se pudo obtener el token de acceso.",
                    "type": "danger",
                    "sticky": True,
                }
            }

        url = f"https://api.mercadolibre.com/items/{publication_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "price": float(self.new_price)
        }

        _logger.info("[ML-PRICE] Enviando PUT a %s con payload: %s", url, payload)

        try:
            response = requests.put(url, headers=headers, data=json.dumps(payload))

            if response.status_code == 200:
                product.write({'mercado_libre_price': self.new_price})
                _logger.info("[ML-PRICE] Precio actualizado correctamente en MercadoLibre a %s", self.new_price)

                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": "Precio actualizado correctamente",
                        "message": f"Se actualizó a {self.new_price}",
                        "type": "success",
                        "sticky": False,
                        "next": {"type": "ir.actions.act_window_close"},
                    }
                }
            else:
                _logger.error("[ML-PRICE] Error al actualizar precio. Código %s, respuesta: %s", response.status_code, response.text)
                raise Exception(f"{response.status_code} - {response.text}")

        except Exception as e:
            _logger.exception("[ML-PRICE] Excepción al actualizar precio en ML")
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Error al actualizar precio",
                    "message": str(e),
                    "type": "danger",
                    "sticky": True,
                }
            }

class ChangeMeliStatusWizard(models.TransientModel):
    _name = 'change.meli.status.wizard'
    _description = 'Cambiar Estado de Publicación ML'

    product_id = fields.Many2one(
        'product.template', 
        string='Producto', 
        required=True, 
        default=lambda self: self.env.context.get('active_id')
    )
    current_status = fields.Char(string="Estado Actual", readonly=True)
    next_status = fields.Selection([
        ('active', 'Activo'),
        ('paused', 'Pausado')
    ], string="Nuevo Estado", readonly=True)

    def action_confirm_change(self):
        self.ensure_one()
        product = self.product_id

        _logger.info("[ML-STATUS] Iniciando cambio de estado para producto: %s (ID: %s)", product.name, product.id)
        _logger.info("[ML-STATUS] Estado actual: %s | Próximo estado: %s", self.current_status, self.next_status)

        if not product.meli_product_id:
            _logger.error("[ML-STATUS] No se encontró meli_product_id.")
            raise UserError("No se encuentra el código de publicación.")

        instance = product.instance_id
        instance.get_access_token()
        access_token = instance.meli_access_token

        if not access_token:
            _logger.error("[ML-STATUS] No se obtuvo token de acceso para la instancia %s", instance.name)
            raise UserError("Token de acceso inválido.")

        url = f"https://api.mercadolibre.com/items/{product.meli_product_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {"status": self.next_status}

        try:
            _logger.info("[ML-STATUS] Enviando PUT a %s con payload: %s", url, payload)
            response = requests.put(url, headers=headers, data=json.dumps(payload))

            if response.status_code == 200:
                _logger.info("[ML-STATUS] Estado actualizado correctamente en ML.")
                product.meli_status = self.next_status
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': "Estado actualizado",
                        'message': f"La publicación fue cambiada a '{self.next_status}'.",
                        'type': 'success',
                        'next': {'type': 'ir.actions.client', 'tag': 'reload'},
                    }
                }
            else:
                _logger.error("[ML-STATUS] Error al actualizar estado: %s", response.text)
                raise UserError(f"Error al actualizar el estado en ML: {response.status_code} - {response.text}")

        except Exception as e:
            _logger.exception("[ML-STATUS] Excepción inesperada al cambiar estado.")
            raise UserError(f"Ocurrió un error al cambiar el estado: {str(e)}")

class UpdateMeliPublicationWizard(models.TransientModel):
    _name = 'update.meli.publication.wizard'
    _description = 'Actualizar publicación MercadoLibre'

    product_id = fields.Many2one(
        'product.template', 
        string='Producto', 
        required=True, 
        default=lambda self: self.env.context.get('active_id')
    )

    update_title = fields.Boolean("Título")
    update_price = fields.Boolean("Precio")
    update_stock = fields.Boolean("Stock")
    update_image = fields.Boolean("Imagen principal")
    update_description = fields.Boolean("Descripción")
    
    def action_confirm_update(self):
        self.ensure_one()
        product = self.product_id

        _logger.info("[ML-UPDATE] Iniciando actualización de publicación para producto: %s (ID: %s)", product.name, product.id)

        if not product.meli_product_id or not product.instance_id:
            _logger.error("[ML-UPDATE] Producto sin código de publicación o sin instancia ML.")
            raise UserError("Faltan datos esenciales para actualizar la publicación.")

        product.instance_id.get_access_token()
        access_token = product.instance_id.meli_access_token
        if not access_token:
            _logger.error("[ML-UPDATE] Token de acceso inválido para la instancia %s", product.instance_id.name)
            raise UserError("Token de acceso inválido.")

        url = f"https://api.mercadolibre.com/items/{product.meli_product_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {}

        if self.update_title:
            payload['title'] = product.name
            _logger.info("[ML-UPDATE] Marcado para actualizar título: %s", product.name)

        if self.update_price:
            payload['price'] = product.mercado_libre_price
            _logger.info("[ML-UPDATE] Marcado para actualizar precio: %s", product.mercado_libre_price)

        if self.update_stock:
            stock_qty = int(sum(product.product_variant_ids.mapped('qty_available')))
            payload['available_quantity'] = stock_qty
            _logger.info("[ML-UPDATE] Marcado para actualizar stock: %s", stock_qty)

        if self.update_description:
            description = product.description_sale or product.name
            payload['description'] = description
            _logger.info("[ML-UPDATE] Marcado para actualizar descripción.")

        if self.update_image and product.image_1920:
            _logger.info("[ML-UPDATE] Marcado para actualizar imagen.")
            image_url = self.upload_image_to_meli(product.image_1920, access_token)
            if image_url:
                payload['pictures'] = [{'source': image_url}]
                _logger.info("[ML-UPDATE] Imagen subida exitosamente: %s", image_url)
            else:
                _logger.error("[ML-UPDATE] No se pudo subir la imagen.")
                raise UserError("No se pudo subir la imagen a MercadoLibre.")

        if not payload:
            _logger.warning("[ML-UPDATE] No se seleccionó ningún campo para actualizar.")
            raise UserError("No se seleccionó ningún campo para actualizar.")

        try:
            _logger.info("[ML-UPDATE] Enviando PUT a %s con payload: %s", url, json.dumps(payload))
            res = requests.put(url, headers=headers, data=json.dumps(payload))

            if res.status_code in [200, 202]:
                _logger.info("[ML-UPDATE] Publicación actualizada correctamente en MercadoLibre.")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': "Actualización exitosa",
                        'message': "La publicación ha sido actualizada correctamente.",
                        'type': 'success',
                        'next': {'type': 'ir.actions.client', 'tag': 'reload'},
                    }
                }
            else:
                _logger.error("[ML-UPDATE] Error al actualizar publicación: %s", res.text)
                raise UserError(f"Error {res.status_code}: {res.text}")

        except Exception as e:
            _logger.exception("[ML-UPDATE] Excepción inesperada durante la actualización.")
            raise UserError(f"Error inesperado al actualizar publicación: {str(e)}")

    def upload_image_to_meli(self, image_binary, access_token):
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/octet-stream"
            }
            img_data = base64.b64decode(image_binary)
            _logger.info("[ML-UPDATE] Enviando imagen a MercadoLibre...")
            res = requests.post("https://api.mercadolibre.com/pictures", headers=headers, data=img_data)

            if res.status_code == 201:
                secure_url = res.json().get('secure_url') or res.json().get('url')
                _logger.info("[ML-UPDATE] Imagen subida correctamente. URL: %s", secure_url)
                return secure_url
            else:
                _logger.warning("[ML-UPDATE] Error al subir imagen: %s", res.text)
        except Exception as e:
            _logger.exception("[ML-UPDATE] Excepción al subir imagen.")
        return False
