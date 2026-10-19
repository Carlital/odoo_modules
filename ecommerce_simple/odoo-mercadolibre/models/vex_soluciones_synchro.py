from odoo import fields, models, api
#from odoo.addons.queue_job.job import job
from datetime import datetime
import requests
import json
import base64
import time
import logging
_logger = logging.getLogger(__name__)
class VexSynchro(models.Model):
    _name="vex.synchro"

    """ @job
    def process_import_line(self, import_line_id):
        import_line = self.env['vex.import_line'].browse(import_line_id)
        if import_line.action == 'order':
            self.sync_order(import_line)
        elif import_line.action == 'product':
            self.sync_product(import_line) """

    def sync_import(self):
        count = 0  # Contador de iteraciones

        ## Updateamos todos los tokens de todas las instancias
        
        for instance in self.env['vex.instance'].search([]):
            if instance.store_type == 'mercadolibre':
                _logger.info("Checking Tokens for Mercado Libre instance")
                self.update_token(instance)


        #time.sleep(100000)
        while count < 19:
            #_logger.info("Iniciando ciclo de sincronización...")
            try:
                import_line_id = self.env['vex.import_line'].search(
                    [
                        ('status', 'in', ['pending']),  
                        ('store_type', '=', 'mercadolibre'),
                        ('instance_id', '=', 10)
                    ],
                    order='id DESC',  
                    limit=1          
                )
                if import_line_id:        
                    if import_line_id.action == 'product':
                        self.sync_product(import_line_id)
                        count += 1  # Incrementa el contador si se sincroniza un producto

                    elif import_line_id.action == 'order':
                        dato = self.sync_order(import_line_id)
                        if dato == "pass":
                            _logger.info("PASS DETECTED")
                            # Si se detecta 'pass', se mantiene el contador igual
                            continue  # Salta al siguiente ciclo sin incrementar
                        else:
                            count += 1  # Incrementa el contador si no es 'pass'
                else:
                    # Si no se encuentra ninguna línea de importación, se puede incrementar el contador para evitar un ciclo infinito
                    count += 1
            except Exception as e:
                _logger.error(f"Error en el proceso de sincronización: {str(e)}")
                # Incrementa el contador para evitar que el ciclo quede atrapado si hay un error
                count += 1

    """ def sync_import(self):
        lines = self.env['vex.import_line'].search([
            ('status', '=', 'pending'),
            ('store_type', '=', 'mercadolibre')
        ], limit=100)  # puedes aumentar este número

        for line in lines:
            self.process_import_line.delay(self, line.id) """

    def _create_or_update_stock(self, product_id, stock_qty, stock_location, debug=False):
        """
        Crea o actualiza el stock de un producto en una ubicación específica.
        Si la ubicación no existe, la crea con el nombre proporcionado.

        :param product_id: ID del producto.
        :param stock_qty: Cantidad de stock a establecer.
        :param stock_location: Nombre de la ubicación donde se debe actualizar/crear el stock.
        :param debug: Si es True, activa los logs para esta función.
        """
        log = _logger.info if debug else lambda *args, **kwargs: None  # Log solo si debug es True

        log("Iniciando proceso para actualizar/crear stock para el producto ID: %s en la ubicación: %s", product_id, stock_location)
        _logger.info("1")
        StockQuant = self.env['stock.quant'].sudo()
        StockLocation = self.env['stock.location'].sudo()
        Product = self.env['product.product'].sudo()

        # Verificar si el producto existe
        product = Product.browse(product_id)
        if not product.exists():
            _logger.error("No se encontró un producto con el ID: %s", product_id)  # Siempre log de error
            raise ValueError(f"No se encontró un producto con el ID: {product_id}")
        _logger.info("2")
        log("Producto encontrado: %s (ID: %s)", product.name, product.id)

        # Buscar o crear la ubicación
        location = StockLocation.search([('name', '=', stock_location)], limit=1)
        if not location:
            log("La ubicación '%s' no existe. Creándola ahora.", stock_location)
            location = StockLocation.create({
                'name': stock_location,
                'usage': 'internal',
            })
            log("Ubicación creada con éxito: %s (ID: %s)", location.name, location.id)
        _logger.info("3")
        location_id = location.id
        log("Ubicación seleccionada: %s (ID: %s)", location.complete_name, location_id)

        # Buscar el stock.quant para el producto y la ubicación
        quant = StockQuant.search([('product_id', '=', product.id), ('location_id', '=', location_id)], limit=1)
        _logger.info("4")
        if quant:
            log("Se encontró un stock.quant existente. Actualizando cantidad de %s a %s", quant.quantity, stock_qty)
            quant.quantity = stock_qty
        else:
            log("No se encontró un stock.quant para el producto %s en la ubicación %s. Creando uno nuevo.", product.name, location.complete_name)
            StockQuant.create({
                'product_id': product.id,
                'location_id': location_id,
                'quantity': stock_qty,
            })
            log("Nuevo stock.quant creado para el producto %s con cantidad %s en la ubicación %s.", product.name, stock_qty, location.complete_name)
        _logger.info("5")
        log("Proceso de actualización/creación de stock completado con éxito.")


    
    def update_token(self, instance):
        access_token = instance.meli_access_token
        user_info_url = 'https://api.mercadolibre.com/users/me'
        res = requests.get(user_info_url, params={'access_token': access_token})

        if res.status_code == 200:
            _logger.info("Token up to date")
            pass
        else:
            url = 'https://api.mercadolibre.com/oauth/token?grant_type=authorization_code&client_id={}&client_secret={}&code={}&redirect_uri={}'.format(instance.meli_app_id, instance.meli_secret_key, instance.meli_server_code,instance.meli_redirect_uri)

            _logger.info("Getting acces token")
            if instance.meli_refresh_token:
                _logger.info("Refresh token logic")
                url = 'https://api.mercadolibre.com/oauth/token'
                data = {
                    'grant_type': 'refresh_token',
                    'client_id': instance.meli_app_id,
                    'client_secret': instance.meli_secret_key,
                    'refresh_token': instance.meli_refresh_token  # tUse the refresh_token stored in the instance
                }

                # Make the POST request with the required parameters
                try:
                    _logger.info("URL: %s", url)
                    _logger.info(f"trans: {data}")
                    response = requests.post(url, data=data)
                    _logger.info(f"Nuevos tokens {response.text}")
                    if response.status_code == 200:
                        json_obj = json.loads(response.text)
                        if 'access_token' in json_obj:
                            _logger.info(f" { json_obj['access_token']}  <--->   {json_obj['refresh_token']}")
                            instance.sudo().write({'access_token': json_obj['access_token']})
                            instance.sudo().write({'refresh_token': json_obj['refresh_token']})

                            _logger.info("Refreshed token")
                    else:                        
                        _logger.error(f"Error refreshing Access Token. Response code:{response.status_code} - {response.text}")
                except Exception as ex:
                    _logger.error(f"Error refreshing Access Token.{ex}")


                return
            try:
                response = requests.post(url)
                _logger.info("URL: %s", url) 
                if response.status_code == 200:
                    json_obj = json.loads(response.text)
                    if 'access_token' in json_obj:
                        self.write({
                            'access_token': json_obj['access_token'],
                            'refresh_token': json_obj['refresh_token'],
                        })
                else:                    
                    _logger.error(response.text)
            except Exception as ex:
                _logger.error(f"Error obtaining Access Token. {ex}")
            

    def sync_product(self, import_line_id):
        _logger.info(import_line_id.description)

        log_id = self.create_log(import_line_id.description)

        try:
            start_time = datetime.today()
            headers = self._get_headers(import_line_id.instance_id.meli_access_token)
            url_item = f"https://api.mercadolibre.com/items?ids={import_line_id.description}"

            response_item = requests.get(url_item, headers=headers)
            if response_item.status_code != 200:
                raise Exception(f"Error al obtener el item: {response_item.text}")

            items = json.loads(response_item.text)

            for item in items:
                self.process_item(item, import_line_id, headers, start_time)

            import_line_id.write({'status': 'done'})
            log_id.write({'state': 'done'})
        except Exception as ex:
            _logger.error(f"Error en sync_product: {ex}")
            import_line_id.write({'status': 'error'})
            log_id.write({'state': 'error'})
        finally:
            end_time = datetime.today()
            import_line_id.write({'start_date': start_time, 'end_date': end_time})
            log_id.write({'start_date': start_time, 'end_date': end_time})


    def create_log(self, description):
        return self.env['vex.meli.logs'].create({
            'description': description,
            'action_type': 'Product',
            'vex_restapi_list_id': self.env.ref('odoo-mercadolibre.meli_action_products').id
        })


    def _get_headers(self, access_token):
        return {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Bearer {access_token}'
        }


    def process_item(self, item, import_line_id, headers, start_time):
        log_product_id = self.create_log(import_line_id.description)
        state = True
        msg = ""
        _logger.info("INSTANCE %s",import_line_id.instance_id.id)
        if item['code'] != 200:
            msg = f"Request error: {item['code']}"
            _logger.warning(msg)
            state = False
            log_product_id.write({'state': 'error', 'description': msg})
            return
        
        item_data = item['body']
        existing_product_id = self._find_existing_product(item_data['id'], import_line_id.instance_id.id)
        attributes, ml_reference = self._process_attributes(item_data['attributes'])
        attribute_value_tuples = self._create_or_update_attributes(attributes, import_line_id.instance_id.id)

        image_1920 = self._fetch_image(item_data['pictures']) if import_line_id.images_import else None
        category_id = self._ensure_category(item_data['category_id'], headers, import_line_id.instance_id.id)

        sku_id = self._get_or_create_sku(ml_reference, import_line_id.instance_id.id)
        stock_location_obj = self._get_stock_location(item_data['shipping']['logistic_type'])

        marketplace_fee = self._get_marketplace_fee(headers, item_data['price'], item_data['listing_type_id'], item_data['category_id'], import_line_id.instance_id.id)
        _logger.info('marketplace_fee%s',marketplace_fee)
        
        product_values = self._prepare_product_values(
            item_data, category_id, image_1920, attribute_value_tuples,
            sku_id, stock_location_obj, ml_reference, marketplace_fee, import_line_id
        )

        if existing_product_id:
            msg = "Actualizando producto"
            _logger.info(msg)
            existing_product_id.write({'attribute_line_ids': [(5, 0, 0)]})
            existing_product_id.write(product_values)
        else:
            msg = "Creando producto"
            existing_product_id = self.env['product.template'].create(product_values)

        self._create_or_update_group_product(existing_product_id, item_data, category_id,
                                            sku_id, ml_reference, image_1920, import_line_id.instance_id.id)

        if import_line_id.stock_import:
            self._update_stock(existing_product_id, item_data)

        log_product_id.write({
            'state': 'done' if state else 'error',
            'start_date': start_time,
            'end_date': datetime.today(),
            'description': msg
        })

        # Procesar atributos y valores
        all_attributes = {}
        for variation in item_data.get('variations', []):
            for attr in variation.get('attribute_combinations', []):
                attr_name = attr['name']
                attr_value = attr['value_name']

                attribute = self.env['product.attribute'].search([('name', '=', attr_name)], limit=1)
                if not attribute:
                    attribute = self.env['product.attribute'].create({'name': attr_name})

                value = self.env['product.attribute.value'].search([
                    ('name', '=', attr_value),
                    ('attribute_id', '=', attribute.id)
                ], limit=1)
                if not value:
                    value = self.env['product.attribute.value'].create({
                        'name': attr_value,
                        'attribute_id': attribute.id
                    })

                all_attributes.setdefault(attribute.id, set()).add(value.id)

        # Agregar líneas de atributo al template
        attribute_lines = []
        for attr_id, value_ids in all_attributes.items():
            attribute_lines.append((0, 0, {
                'attribute_id': attr_id,
                'value_ids': [(6, 0, list(value_ids))]
            }))

        existing_product_id.write({'attribute_line_ids': [(5, 0, 0)] + attribute_lines})

        # Generar o actualizar variantes
        for variation in item_data.get('variations', []):
            sku = variation.get('seller_custom_field') or variation.get('id')
            combination = variation.get('attribute_combinations', [])
            value_ids = []

            for attr in combination:
                value = self.env['product.attribute.value'].search([
                    ('name', '=', attr['value_name']),
                    ('attribute_id.name', '=', attr['name'])
                ], limit=1)
                if value:
                    value_ids.append(value.id)

            # Buscar variante por combinación exacta
            variant = None
            for p in existing_product_id.product_variant_ids:
                variant_value_ids = set(p.product_template_variant_value_ids.mapped('product_attribute_value_id.id'))
                if set(value_ids) == variant_value_ids:
                    variant = p
                    break

            if not variant:
                _logger.warning(f"No se encontró variante para combinación: {value_ids}")
                continue

            # Obtener imagen específica de la variante
            image_variant = False
            image_url = None
            if variation.get('picture_ids'):
                pic_id = variation['picture_ids'][0]
                for image in item_data['pictures']:
                    if image['id'] == pic_id:
                        image_url = image.get('url')
                        break

                if image_url:
                    try:
                        response = requests.get(image_url)
                        if response.status_code == 200:
                            image_variant = base64.b64encode(response.content).decode('utf-8')
                    except Exception as e:
                        _logger.warning(f"Error obteniendo imagen de variante: {e}")

            # Actualizar datos de la variante
            variant.write({
                'default_code': sku,
                'list_price': variation.get('price'),
                'image_1920': image_variant or False,
            })

            # Actualizar stock si está activado
            if import_line_id.stock_import:
                self._create_or_update_stock(
                    product_id=variant.id,
                    stock_qty=variation.get('available_quantity', 0),
                    stock_location='Stock',
                    debug=False
                )

        _logger.info(f"Producto '{item_data.get('title')}' importado con variantes y stock correctamente.")
        """2 used_attribute_ids = set()
        for variation in item_data.get('variations', []):
            for attr in variation.get('attribute_combinations', []):
                attr_obj = self.env['product.attribute'].search([('name', '=', attr['name'])], limit=1)
                if attr_obj:
                    used_attribute_ids.add(attr_obj.id)

        # 1. Crear atributos sin valores
        attribute_lines = []
        for attr_id in used_attribute_ids:
            attribute_lines.append((0, 0, {
                'attribute_id': attr_id,
                'value_ids': [(6, 0, [])],  # Sin valores para evitar combinaciones
            }))
        existing_product_id.write({'attribute_line_ids': [(5, 0, 0)] + attribute_lines})

        # 2. Eliminar variantes automáticas creadas por Odoo
        unused_variants = existing_product_id.product_variant_ids.filtered(
            lambda v: not self.env['stock.move'].search_count([('product_id', '=', v.id)])
        )
        if unused_variants:
            _logger.info(f"Eliminando {len(unused_variants)} variantes no utilizadas del producto {existing_product_id.name}")
            unused_variants.unlink()

        # 3. Crear variantes manualmente solo con combinaciones reales
        ProductProduct = self.env['product.product']
        for variation in item_data.get('variations', []):
            sku = variation.get('seller_custom_field') or variation.get('id')
            combination = variation.get('attribute_combinations', [])
            value_ids = []

            for attr in combination:
                value = self.env['product.attribute.value'].search([
                    ('name', '=', attr['value_name']),
                    ('attribute_id.name', '=', attr['name'])
                ], limit=1)
                if value:
                    value_ids.append(value.id)

            if not value_ids:
                continue

            # Crear la variante manualmente
            new_variant = ProductProduct.create({
                'product_tmpl_id': existing_product_id.id,
                'product_template_attribute_value_ids': [
                    (0, 0, {'product_attribute_value_id': val_id})
                    for val_id in value_ids
                ],
                'default_code': sku,
                'list_price': variation.get('price'),
            })

            # Imagen por variante
            image_variant = False
            image_url = None
            if variation.get('picture_ids'):
                pic_id = variation['picture_ids'][0]
                for image in item_data['pictures']:
                    if image['id'] == pic_id:
                        image_url = image.get('url')
                        break

                if image_url:
                    try:
                        response = requests.get(image_url)
                        if response.status_code == 200:
                            image_variant = base64.b64encode(response.content).decode('utf-8')
                    except Exception as e:
                        _logger.warning(f"Error obteniendo imagen de variante: {e}")

            if image_variant:
                new_variant.write({'image_1920': image_variant})

            # Stock por variante
            if import_line_id.stock_import:
                self._create_or_update_stock(
                    product_id=new_variant.id,
                    stock_qty=variation.get('available_quantity', 0),
                    stock_location='Stock',
                    debug=False
                )
        _logger.info(f"Producto '{item_data.get('title')}' importado con variantes y stock correctamente.")   """ 
        """ # Procesar variantes si existen 3
        variations = item_data.get('variations', [])
        ProductProduct = self.env['product.product'].sudo()
        Attribute = self.env['product.attribute'].sudo()
        AttributeValue = self.env['product.attribute.value'].sudo()

        if variations:
            _logger.info("Procesando %s variantes para el producto %s", len(variations), existing_product_id.name)
            
            for variation in variations:
                variant_attrs = variation.get('attribute_combinations', [])
                image_variant = False
                image_url = None
                for image in item_data['pictures']:
                    if image['id'] == variation['picture_ids'][0]:
                        image_url = image.get('url')
                        break

                if image_url:
                    response = requests.get(image_url)
                    if response.status_code == 200:
                        image_variant = base64.b64encode(response.content).decode('utf-8')

                attr_value_ids = []

                for attr in variant_attrs:
                    attr_name = attr.get('name')
                    attr_value = attr.get('value_name')

                    if not attr_name or not attr_value:
                        continue

                    attribute = Attribute.search([('name', '=', attr_name)], limit=1)
                    if not attribute:
                        attribute = Attribute.create({'name': attr_name})

                    value = AttributeValue.search([
                        ('name', '=', attr_value),
                        ('attribute_id', '=', attribute.id)
                    ], limit=1)
                    if not value:
                        value = AttributeValue.create({
                            'name': attr_value,
                            'attribute_id': attribute.id
                        })

                    attr_value_ids.append((0, 0, {
                        'attribute_id': attribute.id,
                        'value_id': value.id
                    }))

                obj_variant = {
                        "product_tmpl_id": existing_product_id.id,
                        'instance_id': import_line_id.instance_id.id, 
                        'ml_variation_id': variation['id'],
                        "list_price": variation['price'],
                        "image_1920": image_variant,
                        'product_template_attribute_value_ids': [(6, 0, [v[2]['value_id'] for v in attr_value_ids])]
                    }
                # Crear la variante si no existe
                variant = ProductProduct.search([
                    ('product_tmpl_id', '=', existing_product_id.id),
                    ('ml_variation_id', '=', variation['id'])  # Asumiendo que este campo lo defines tú
                ], limit=1)

                if not variant:
                    variant = ProductProduct.create(obj_variant)
                else:
                    ProductProduct.write(obj_variant)

                # Actualizar stock individual para variante
                if import_line_id.stock_import:
                    _logger.info("8")

                    available_qty = variation.get('available_quantity', 0)

                    self._create_or_update_stock(variant.id, available_qty, stock_location_obj)

                _logger.info("9") """


    def _find_existing_product(self, meli_code, instance_id):
        return self.env['product.template'].search([
            ('meli_code', '=', meli_code),
            ('instance_id', '=', instance_id)
            #,('active', '=', True)
        ], limit=1)


    def _process_attributes(self, attributes_list):
        attributes = []
        ml_reference = None

        for product in attributes_list:
            if product['id'] == 'SELLER_SKU':
                ml_reference = product['value_name']
            else:
                attributes.append({
                    'name': product['name'],
                    'meli_code': product['id'],
                    'value_name': product['value_name']
                })

        return attributes, ml_reference


    def _create_or_update_attributes(self, attributes, instance_id):
        attribute_value = []

        for attr in attributes:
            attribute = self.env['product.attribute'].search([
                ('meli_code', '=', attr['meli_code']),
                ('instance_id', '=', instance_id)
            ], limit=1)

            if not attribute:
                attribute = self.env['product.attribute'].create({
                    'name': attr['name'],
                    'meli_code': attr['meli_code'],
                    'instance_id': instance_id
                })

            if attr['value_name']:
                value = self.env['product.attribute.value'].search([
                    ('name', '=', attr['value_name']),
                    ('attribute_id', '=', attribute.id),
                    ('instance_id', '=', instance_id)
                ], limit=1)

                if not value:
                    value = self.env['product.attribute.value'].create({
                        'name': attr['value_name'],
                        'attribute_id': attribute.id,
                        'instance_id': instance_id
                    })

                attribute_value.append((attribute.id, value.id))

        return [(0, 0, {'attribute_id': attr_id, 'value_ids': [(6, 0, [val_id])]}) for attr_id, val_id in attribute_value] if attribute_value else False


    def _fetch_image(self, pictures):
        if not pictures:
            return None

        try:
            image_url = pictures[0]['url']
            image_content = requests.get(image_url).content
            return base64.b64encode(image_content).decode('utf-8') if image_content else None
        except Exception as e:
            _logger.warning(f"Error al obtener imagen: {e}")
            return None


    def _ensure_category(self, category_id, headers, instance_id):
        category = self.env['product.category'].search([
            ('meli_code', '=', category_id),
            ('instance_id', '=', instance_id)
        ], limit=1)

        if not category:
            _logger.info(f"Categoría {category_id} no existe. Creándola...")
            wizard = self.env['vex.import.wizard']
            wizard.synchronize_specific_category(category_id, headers, instance_id)
            category = self.env['product.category'].search([
                ('meli_code', '=', category_id),
                ('instance_id', '=', instance_id)
            ], limit=1)

        return category or self.env.ref('odoo-mercadolibre.category_not_found')


    def _get_or_create_sku(self, ml_reference, instance_id):
        if not ml_reference:
            return False

        sku = self.env['vex.sku'].search([
            ('name', '=', ml_reference),
            ('instance_id', '=', instance_id)
        ], limit=1)

        return sku or self.env['vex.sku'].create({'name': ml_reference, 'instance_id': instance_id})


    def _get_stock_location(self, logistic_type):
        return "FULL Mercado Libre Default" if logistic_type == "fulfillment" else "Default Mercado Libre"

    def _get_marketplace_fee(self, headers, price, listing_type_id, category_id, instance_id):
        instance = self.env['vex.instance'].search([('id', '=', instance_id)])
        code_country = instance.meli_country
        url = f"https://api.mercadolibre.com/sites/{code_country}/listing_prices?price={price}&listing_type_id={listing_type_id}&category_id={category_id}"
        _logger.info(url)
        response = requests.get(url, headers=headers)
        market_fee = 0.0
        if response.status_code == 200:
            res_json = json.loads(response.text)
            market_fee = res_json['sale_fee_amount']
        else:
            _logger.info(response.text)
        return market_fee
    
    # def _prepare_product_values(self, item_data, category_id, image_1920, attribute_value_tuples, sku_id, stock_location_obj, ml_reference, marketplace_fee, import_line_id):
    #     return {
    #         'categ_id': category_id.id,
    #         'name': item_data['title'],
    #         'list_price': item_data['price'],
    #         'mercado_libre_price': item_data['price'],
    #         'meli_code': item_data['id'],
    #         'default_code': item_data['id'],
    #         'server_meli': True,
    #         'detailed_type': 'product',
    #         'image_1920': image_1920,
    #         'ml_reference': ml_reference,
    #         'ml_publication_code': item_data['id'],
    #         'meli_category_code': item_data['category_id'],
    #         'meli_status': item_data['status'],
    #         'attribute_line_ids': attribute_value_tuples,
    #         'sku_id': sku_id.id if sku_id else False,
    #         'listing_type_id': item_data['listing_type_id'],
    #         'condition': item_data['condition'],
    #         'permalink': item_data['permalink'],
    #         'thumbnail': item_data['thumbnail'],
    #         'buying_mode': item_data['buying_mode'],
    #         'inventory_id': item_data.get('inventory_id'),
    #         'action_export': 'edit',
    #         'instance_id': import_line_id.instance_id.id,
    #         'stock_type': stock_location_obj,
    #         'upc': next((attr['value_name'] for attr in item_data['attributes'] if attr['id'] == 'GTIN'), None),
    #         'store_type': 'mercadolibre',
    #         'market_fee': marketplace_fee
    #     }
    def _prepare_product_values(self, item_data, category_id, image_1920, attribute_value_tuples, sku_id, stock_location_obj, ml_reference, marketplace_fee, import_line_id):
        ProductTag = self.env['product.meli.tag']
        ProductChannel = self.env['product.meli.channel']
        ProductPicture = self.env['product.meli.picture']
        ProductAttribute = self.env['product.meli.attribute']
        ProductVariation = self.env['product.meli.variation']
        Marketplace = self.env['product.marketplace']

        # Tags
        tag_ids = []
        for tag in item_data.get('tags', []):
            tag_rec = ProductTag.search([('name', '=', tag)], limit=1)
            if not tag_rec:
                tag_rec = ProductTag.create({'name': tag})
            tag_ids.append(tag_rec.id)

        # Channels
        channel_ids = []
        for channel in item_data.get('channels', []):
            channel_rec = ProductChannel.search([('name', '=', channel)], limit=1)
            if not channel_rec:
                channel_rec = ProductChannel.create({'name': channel})
            channel_ids.append(channel_rec.id)

        # Pictures
        picture_vals = []
        for picture in item_data.get('pictures', []):
            picture_vals.append((0, 0, {
                'name': picture.get('id'),
                'url': picture.get('secure_url'),
                'size': picture.get('size'),
                'max_size': picture.get('max_size'),
            }))

        # Attributes
        attribute_vals = []
        for attr in item_data.get('attributes', []):
            value_names = [v.get('name') for v in attr.get('values', []) if v.get('name')]
            attribute_vals.append((0, 0, {
                'meli_attribute_id': attr.get('id'),
                'name': attr.get('name'),
                'value_name': ', '.join(value_names),
            }))

        # Variations
        variation_vals = []
        for variation in item_data.get('variations', []):
            combination_names = [c.get('value_name') for c in variation.get('attribute_combinations', []) if c.get('value_name')]
            variation_vals.append((0, 0, {
                'ml_variation_id': variation.get('id'),
                'price': variation.get('price'),
                'available_quantity': variation.get('available_quantity'),
                'sold_quantity': variation.get('sold_quantity'),
                'attribute_names': ', '.join(combination_names),
                'user_product_id': variation.get('user_product_id'),
            }))

        # Marketplace
        ml_marketplace = Marketplace.search([('name', '=', 'mercadolibre')], limit=1)
        if not ml_marketplace:
            ml_marketplace = Marketplace.create({'name': 'mercadolibre'})

        # Producto base
        return {
            'categ_id': category_id.id,
            'name': item_data['title'],
            'list_price': item_data['price'],
            'mercado_libre_price': item_data['price'],
            'meli_code': item_data['id'],
            'default_code': item_data['id'],
            'server_meli': True,
            'detailed_type': 'product',
            'image_1920': image_1920,
            'ml_reference': ml_reference,
            'ml_publication_code': item_data['id'],
            'meli_category_code': item_data['category_id'],
            'meli_status': item_data['status'],
            'attribute_line_ids': attribute_value_tuples,
            'sku_id': sku_id.id if sku_id else False,
            'listing_type_id': item_data['listing_type_id'],
            'condition': item_data['condition'],
            'permalink': item_data['permalink'],
            'thumbnail': item_data['thumbnail'],
            'buying_mode': item_data['buying_mode'],
            'inventory_id': item_data.get('inventory_id'),
            'action_export': 'edit',
            'instance_id': import_line_id.instance_id.id,
            'stock_type': stock_location_obj,
            'upc': next((attr['value_name'] for attr in item_data['attributes'] if attr['id'] == 'GTIN'), None),
            'store_type': 'mercadolibre',
            'market_fee': marketplace_fee,

            # Relaciones
            'meli_tag_ids': [(6, 0, tag_ids)],
            'meli_channel_ids': [(6, 0, channel_ids)],
            'marketplace_ids': [(4, ml_marketplace.id)],
            'meli_pictures_ids': picture_vals,
            'meli_attribute_ids': attribute_vals,
            'meli_variation_ids': variation_vals,
        }


    def _create_or_update_group_product(self, existing_product_id, item_data, category_id, sku_id, ml_reference, image_1920, instance_id):
        if not (sku_id and ml_reference):
            return

        group_product = self.env['vex.group_product'].search([
            ('product_id', '=', existing_product_id.id),
            ('instance_id', '=', instance_id)
        ], limit=1)

        group_values = {
            'name': existing_product_id.name,
            'url': item_data['permalink'],
            'num_publication': existing_product_id.meli_code,
            'product_id': existing_product_id.id,
            'image': image_1920,
            'price': existing_product_id.list_price,
            'categ_id': category_id.id,
            'quantity': item_data['available_quantity'],
            'sku_id': sku_id.id,
            'instance_id': instance_id
        }

        if group_product:
            group_product.write(group_values)
        else:
            self.env['vex.group_product'].create(group_values)


    def _update_stock(self, existing_product_id, item_data):
        _logger.info("Actualizando stock")
        stock_qty = item_data['available_quantity']
        logistic_type = item_data['shipping']['logistic_type']
        stock_location = self._get_stock_location(logistic_type)

        product_variant = self.env['product.product'].search([
            ('product_tmpl_id', '=', existing_product_id.id),
            ('active', '=', True)
        ], limit=1)

        if product_variant:
            self._create_or_update_stock(product_variant.id, stock_qty, stock_location, debug=True)




    def _create_and_post_invoice(self, order, json_order,import_line_id):

        invoice_action = import_line_id.instance_id.invoice_action

        if  invoice_action  == 'no_facturar':                
                _logger.info("No se generará factura para el pedido %s", order.id)
                _logger.info(f"Instancia {import_line_id.instance_id} Valor {import_line_id.instance_id.invoice_action} Nombre {import_line_id.instance_id.name}")
                return                                
            
         # Crear la factura desde el pedido de venta
        invoice = order._create_invoices()

        _logger.info(f"Factura creada con ID: {invoice.id} para la orden de venta {order.id}.")
        invoice.action_post()  # Publicar la factura
        _logger.info(f"Factura {invoice.id} publicada.")

        # Registrar comisiones de Mercado Libre y envío
        commission_journal = self.env['account.journal'].search([('type', '=', 'general')], limit=1)
        commission_account = self.env['account.account'].search([('code', '=', 6100)], limit=1)
        shipping_account = self.env['account.account'].search([('code', '=', 6200)], limit=1)

        if not commission_account or not shipping_account:
            _logger.error("No se encontraron las cuentas contables de comisión o envío. Configúralas primero.")
            raise ValueError("Cuentas contables de comisión o envío no configuradas.")


        _logger.info("Iniciando la creación de asientos contables para las comisiones...")
        commission_move = self.env['account.move'].create({
            'journal_id': commission_journal.id,
            'line_ids': [
                # Registro de comisión por envío ($120)
                (0, 0, {
                    'account_id': shipping_account.id,
                    'debit': order.shipping_cost,
                    'credit': 0.0,
                }),
                # Registro de comisión de Mercado Libre ($70)
                (0, 0, {
                    'account_id': commission_account.id,
                    'debit': order.marketplace_fee,
                    'credit': 0.0,
                }),
                # Contrapartida (afecta la cuenta por cobrar)
                (0, 0, {
                    'account_id': self.env['account.account'].search([('code', '=', 1100)], limit=1).id,
                    'debit': 0.0,
                    'credit': order.marketplace_fee+order.shipping_cost,  # Total de comisiones
                }),
            ]
        })
        _logger.info(f"Asientos contables creados con ID: {commission_move.id}")
        _logger.debug(f"Detalles de los asientos contables: {commission_move.line_ids}")
        _logger.info(f"Respectivamente  {order.shipping_cost}     {order.marketplace_fee}")

        # Publicar los asientos contables
        try:
            commission_move.action_post()
            _logger.info(f"Asientos contables para las comisiones publicados exitosamente: {commission_move.id}")
        except Exception as e:
            _logger.error(f"Error al publicar los asientos contables de comisiones: {e}")
            raise


        _logger.info("Registrando el pago")
        self.registrar_pago(invoice)

        
    def registrar_pago(self, invoice):
        """
        Registra un pago para una factura específica.

        :param invoice: Registro de la factura (account.move) a pagar.
        """
        try:
            # Registrar el pago de la factura
            payment = self.env['account.payment.register'].with_context(
                active_model='account.move',
                active_ids=invoice.ids
            ).create({
                'amount': invoice.amount_residual,  # Monto pendiente de la factura
                'journal_id': self.env['account.journal'].search([('type', '=', 'cash')], limit=1).id,  # Diario de efectivo
                'payment_date': fields.Date.context_today(self),  # Fecha actual
            })
            payment._create_payments()  # Procesar y registrar el pago
            _logger.info(f"Pago registrado y conciliado para la factura {invoice.id}.")
            return payment
        except Exception as e:
            _logger.error(f"Error al registrar el pago para la factura {invoice.id}: {str(e)}", exc_info=True)
            raise


    def confirm_delivery(self, sale_order_id):
        picking_origin = f"S{sale_order_id}"
        _logger.info(f"Iniciando confirmación de entrega para la orden de venta: {picking_origin}")

        # Buscar los pickings asociados
        pickings = self.env['stock.picking'].search([('origin', '=', picking_origin)])
        if not pickings:
            _logger.warning(f"No se encontraron albaranes asociados a la orden de venta: {picking_origin}")
            return False

        for picking in pickings:
            _logger.info(f"Procesando picking: {picking.name} con estado inicial: {picking.state}")

            if picking.state not in ['done', 'cancel']:
                if picking.state in ['draft', 'waiting']:
                    _logger.info(f"Intentando confirmar el picking: {picking.name}")
                    picking.action_confirm()
                    _logger.info(f"Estado después de confirmar: {picking.state}")

                if picking.state == 'confirmed':
                    _logger.info(f"Intentando asignar productos al picking: {picking.name}")
                    picking.action_assign()  # Reservar productos automáticamente
                    _logger.info(f"Estado después de intentar asignar: {picking.state}")
                    reserved_quantities = sum(
                        line.reserved_availability for line in picking.move_ids
                    )
                    demanded_quantities = sum(
                        line.product_uom_qty for line in picking.move_ids
                    )
                    _logger.info(
                        f"Picking {picking.name}: {reserved_quantities} de {demanded_quantities} productos reservados."
                    )

                    if picking.state == 'assigned':
                        _logger.info(f"Intentando marcar como entregado el picking: {picking.name}")
                        picking._action_done()
                        _logger.info(f"Estado después de marcar como entregado: {picking.state}")
                    else:
                        _logger.warning(
                            f"No se pudo marcar como entregado el picking {picking.name} porque no está asignado."
                        )
                else:
                    _logger.warning(
                        f"El picking {picking.name} no está en estado asignado o confirmado. Estado actual: {picking.state}"
                    )

                # Validar si el picking realmente está en estado "done"
                if picking.state == 'done':
                    _logger.info(f"Picking {picking.name} correctamente entregado.")
                else:
                    _logger.error(
                        f"Picking {picking.name} aún no está en estado 'done'. Estado actual: {picking.state}."
                    )
            else:
                _logger.warning(f"El picking {picking.name} ya está en estado '{picking.state}'. No se procesará.")

        _logger.info(f"Finalización de la confirmación de entrega para la orden de venta: {picking_origin}")
        return True
        
    def _get_or_create_partner_from_meli(self, buyer_info, instance_id, headers):
        """Retrieve or create partner from MercadoLibre buyer data."""
        nickname = buyer_info.get("nickname")
        partner = self.env['res.partner'].search([
            ('nickname', '=', nickname),
            ('instance_id', '=', instance_id.id)
        ], limit=1)

        if not partner:
            buyer_id = buyer_info.get("id")
            url = f"https://api.mercadolibre.com/users/{buyer_id}"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                buyer_data = response.json()
                nickname = buyer_data.get("nickname")
                partner = self.env['res.partner'].create({
                    'name': f"{buyer_data.get('first_name', 'Deactivated')} {buyer_data.get('last_name', '')}",
                    'nickname': nickname,
                    'meli_user_id': buyer_id,
                    'l10n_latam_identification_type_id': 1,
                    'instance_id': instance_id.id,
                    'server_meli': True
                })
                _logger.info(f"Created partner for {nickname} ({buyer_id})")
        return partner

    def _get_or_create_product(self, meli_item_id, instance_id, headers):
        """Retrieve or import product based on item ID from MercadoLibre."""
        product_tmpl = self.env['product.template'].search([
            ('default_code', '=', meli_item_id),
            ('instance_id', '=', instance_id.id),
            ('active', '=', True)
        ], limit=1)

        if not product_tmpl:
            import_line = self.env['vex.import_line'].create({
                'stock_import': True,
                'images_import': True,
                'description': meli_item_id,
                'instance_id': instance_id.id,
                'status': 'pending'
            })
            self.env['vex.instance'].sync_product(import_line)
            product_tmpl = self.env['product.template'].search([
                ('default_code', '=', meli_item_id),
                ('instance_id', '=', instance_id.id),
                ('active', '=', True)
            ], limit=1)

        if product_tmpl:
            product = self.env['product.product'].search([
                ('product_tmpl_id', '=', product_tmpl.id),
                ('active', '=', True)
            ], limit=1)
            return product_tmpl, product

        raise ValueError(f"Product {meli_item_id} could not be created or found.")

    def _build_order_lines(self, items, instance_id, headers):
        """Build order lines from MercadoLibre order items."""
        order_lines = []
        for item in items:
            product_tmpl, product = self._get_or_create_product(item['item']['id'], instance_id, headers)
            if not product:
                raise ValueError(f"No product for item {item['item']['id']}")

            line = {
                'product_id': product.id,
                'product_template_id': product_tmpl.id,
                'name': product_tmpl.name,
                'product_uom_qty': item['quantity'],
                'price_unit': item['unit_price'],
                'tax_id': [(5, 0, 0)],
                'display_type': False
            }
            order_lines.append((0, 0, line))
        return order_lines

    def _extract_shipping_data(self, shipping_id, headers):
        """Fetch and return shipping data."""
        shipment_url = f"https://api.mercadolibre.com/shipments/{shipping_id}"
        shipment_response = requests.get(shipment_url, headers=headers)
        if shipment_response.status_code == 200:
            shipment_data = shipment_response.json()
            return shipment_data.get('id'), shipment_data.get('logistic_type', ''), shipment_data.get('status', '')
        return '', '', 'Not Delivered'

    def _categorize_order_status(self, json_order):
        """Categorize order status from JSON data."""
        tags = json_order.get('tags', [])
        payments = json_order.get('payments', [])
        approved = sum(1 for p in payments if p.get('status') == 'approved')
        charged_back = sum(1 for p in payments if p.get('status') == 'charged_back' and p.get('status_detail') == 'reimbursed')

        if approved >= 1 and 'paid' in tags and 'delivered' in tags:
            return 'Completada', True
        if json_order.get('status') == 'cancelled':
            return 'Canceled', False
        if approved >= 1 and 'paid' in tags and 'not_delivered' in tags:
            return 'Pending', False
        if json_order.get('status') == 'partially_refunded':
            return 'Partially Refunded', False
        if approved == 0 and charged_back >= 1:
            return 'Reimbursed', False
        if json_order.get('fulfilled') and 'no_shipping' in tags:
            return 'Completada', True
        return 'No Pagada', False

    def sync_order(self, import_line_id):
        """Main function to sync MercadoLibre orders with Odoo."""
        start_time = datetime.today()
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Bearer {import_line_id.instance_id.meli_access_token}'
        }
        order_ids = import_line_id.description.split(",")

        correct_counter, exists_counter = 0, 0

        for order_id in order_ids:
            sale_order_exist = self.env['sale.order'].search([
                ('meli_code', '=', order_id),
                ('instance_id', '=', import_line_id.instance_id.id)
            ], limit=1)

            if sale_order_exist:
                exists_counter += 1
                continue

            order_url = f"https://api.mercadolibre.com/orders/{order_id}"
            response = requests.get(order_url, headers=headers)
            if response.status_code != 200:
                continue

            json_order = response.json()
            buyer_info = json_order.get('buyer', {})
            partner = self._get_or_create_partner_from_meli(buyer_info, import_line_id.instance_id, headers)
            shipping_id, shipping_type, shipping_status = '', '', 'Not Delivered'

            if json_order.get('shipping', {}).get('id'):
                shipping_id, shipping_type, shipping_status = self._extract_shipping_data(json_order['shipping']['id'], headers)

            order_lines = self._build_order_lines(json_order.get('order_items', []), import_line_id.instance_id, headers)
            order_status, order_is_closed = self._categorize_order_status(json_order)

            order_vals = {
                'meli_code': json_order['id'],
                'partner_id': partner.id,
                'date_order': json_order['date_created'],
                'state': 'sale',
                'server_meli': True,
                'shipping_id': shipping_id,
                'shipping_type': shipping_type,
                'shipping_status': shipping_status,
                'order_line': order_lines,
                'total_paid_amount': json_order.get('paid_amount', 0.0),
                'shipping_cost': sum(p.get('shipping_cost', 0.0) for p in json_order.get('payments', [])),
                'marketplace_fee': sum(p.get('marketplace_fee', 0.0) for p in json_order.get('payments', [])),
                'order_status': order_status,
                'order_is_closed': order_is_closed,
                'instance_id': import_line_id.instance_id.id,
                'tags': ','.join(json_order.get('tags', []))
            }

            order = self.env['sale.order'].create(order_vals)
            correct_counter += 1

        end_time = datetime.today()
        status = 'done' if correct_counter == len(order_ids) else 'obs' if correct_counter > 0 else 'error'
        import_line_id.write({
            'start_date': start_time,
            'end_date': end_time,
            'checks_indicator': f'{correct_counter}/{len(order_ids)}',
            'status': status
        })

        if exists_counter == 20:
            return "pass"


    def get_data_from_api(self, uri, header):
        """
        Función que nos permite consumir un API RestFUL y que nos devuelve la respuesta

        Attributes:
            uri (str): Endpoint donde se va a consumir
            header (str): Cabecera
        """
        response = requests.get(uri, headers=header)

        json_response = False

        if response.status_code != 204:
            json_response = json.loads(response.text)

       #print("response status - order: ", response.status_code)        
       # print("json_response: ", json_response)

        return json_response