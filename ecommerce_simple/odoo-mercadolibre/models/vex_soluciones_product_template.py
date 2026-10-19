# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from werkzeug.urls import url_join
from odoo.http import request

import base64
import requests
import json
import tempfile
import os

class ProductTemplateAttributeLine(models.Model):
    _inherit = 'product.template.attribute.line'

    meli_required = fields.Boolean(string="ML Requerido", help="Indica si el atributo es requerido según la API de Mercado Libre.")
    has_meli_attribute = fields.Boolean(
        string="Has Meli Attribute",
        compute="_compute_has_meli_attribute",
        store=True
    )

    @api.depends('attribute_id.meli_attribute_id')
    def _compute_has_meli_attribute(self):
        for line in self:
            line.has_meli_attribute = bool(line.attribute_id.meli_attribute_id)
    
class VexSolucionesProductInherit(models.Model):
    _inherit = 'product.template'
    
    instance_id = fields.Many2one('vex.instance', string='Instance of')
    instance_image = fields.Image(related='instance_id.image', string="Instance Image", readonly=True)
    
    # PEDRO LOGICA
    image_gallery_ids = fields.Many2many(
        'ir.attachment',
        string='Image Gallery',
        relation='product_template_ir_attachment_rel',
        column1='product_id',
        column2='attachment_id',
        domain=[('res_model', '=', 'product.template')],
        help='Product image gallery'
    )    
    
    meli_id = fields.Char('Id', readonly=True)
    meli_description = fields.Html('Description of Mercado Libre', translate=True)
    
    meli_title = fields.Char('Title')
    meli_sku = fields.Char('Sku')
    meli_site_id = fields.Char('Site id')
    meli_seller_id = fields.Integer('Seller Id')
    meli_category_id = fields.Char('Category Id')
    
    meli_user_product_id = fields.Char('User Product Id')
    meli_official_store_id = fields.Char('Official Store Id')
    meli_price = fields.Float('Price')
    meli_base_price = fields.Float('Base Price')
    meli_original_price = fields.Char('Original Price')
    meli_inventory_id = fields.Char('Inventory Id')
    
    meli_currency_id = fields.Char('Currency Id')
    meli_initial_quantity = fields.Integer('Initial Quantity')
    meli_sold_quantity = fields.Integer('Sold Quantity')
    meli_warranty = fields.Char('Warranty')
    meli_buying_mode = fields.Char('Buying Mode')
    meli_listing_type_id = fields.Char('Listing Type Id')
    
    meli_condition = fields.Char('Condition')
    meli_permalink = fields.Char('Publication link')
    meli_thumbnail = fields.Char('Thumbnail')
    # pictures
    meli_accepts_mercadopago = fields.Boolean('Accepts Mercado Pago') 
    
    meli_free_shipping = fields.Boolean('Free Shipping') # ESTO VA DENTRO DE SHIPPING
    meli_logistic_type = fields.Char('Logistic Typ') # ESTO VA DENTRO DE SHIPPING
    
    meli_status = fields.Selection([
        ('active', 'Active'),
        ('under_review', 'Under Review'),
        ('inactive', 'Inactive'),
    ], string='Status', default='inactive')
    
    meli_catalog_listing = fields.Boolean('Catalog Listing')
    meli_catalog_product_id = fields.Char('Catalog Product Id')
    
    meli_categ_id = fields.Many2one(
        'product.category',
        string='Mercado Libre Category',
        help='Categoría de Mercado Libre vinculada a este producto'
    )
    
    meli_product_channel_ids = fields.Many2many('product.channel', string='Channels')
    
    _sql_constraints = [
        ('meli_id_uniq', 'unique(meli_id)', 'The meli id must be unique')
    ]
    
    has_meli_category_id = fields.Boolean(
        string="Has Mercado Libre Category ID",
        compute='_compute_has_meli_category_id',
        store=True
    )
    
    @api.depends('meli_categ_id.meli_category_id')
    def _compute_has_meli_category_id(self):
        for record in self:
            record.has_meli_category_id = bool(record.meli_categ_id.meli_category_id)
    
    def notify_feature_in_development(self):
        self.ensure_one()
        message = (
            "🚧 Esta función está en construcción! 🚧\n\n"
            "No se pudo crear el producto ni sincronizar con Mercado Libre. "
            "Por favor, asegúrese de que la instancia esté configurada correctamente y vuelva a intentarlo. "
            "¡Gracias por su paciencia! 😊"
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Función en Desarrollo',
                'message': message,
                'type': 'warning',  # Puede ser 'info', 'warning', 'danger', 'success'
                'sticky': False,  # True/False para hacer la notificación persistente
            },
        }
    
    # EXPORT ODOO TO MERCADO LIBRE
    # @api.model
    # def create(self, vals):
    #     record = super(VexSolucionesProduct, self).create(vals)

    #     if not record['name']:
    #         raise UserError("El campo 'name' es obligatorio y no puede estar vacío.")

    #     instance_id = vals.get('instance_id')
    #     if instance_id:
    #         self.export_to_mercado_libre(record, instance_id)

    #     return record
    
    def upload_image_to_mercado_libre(self):
        self.instance_id._log("Iniciando carga de imagen", 'info')

        temp_file_path = None

        try:
            # Obtener la imagen en base64 del campo 'image_base64'
            image_base64 = self.image_1920
            if not image_base64:
                raise UserError("No se encontró ninguna imagen base64 en el registro.")
            
            # Decodificar el base64
            image_data = base64.b64decode(image_base64)
            
            # Guardar la imagen en un archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                temp_file.write(image_data)
                temp_file_path = temp_file.name

            # Subir la imagen a Mercado Libre
            url = 'https://api.mercadolibre.com/pictures/items/upload'
            headers = {
                'Authorization': f'Bearer {self.instance_id.meli_access_token}'
            }
            
            # Enviar el archivo
            with open(temp_file_path, 'rb') as temp_file:
                files = {'file': temp_file}
                try:
                    upload_response = requests.post(url, headers=headers, files=files)
                    upload_response_data = upload_response.json()
                
                    if upload_response.status_code == 201:
                        self.instance_id._log(f"Imagen subida exitosamente. Respuesta: {upload_response_data}", 'info')
                        return upload_response_data
                    else:
                        error_message = f"Error al subir la imagen: {upload_response_data}"
                        self.instance_id._log(error_message, 'error')
                        raise UserError(error_message)
                except requests.exceptions.HTTPError as e:
                    error_message = f"Excepción durante la carga de la imagen: {str(e)}"
                    self.instance_id._log(error_message, 'error')
                    raise UserError(error_message)
        finally:
            # Asegúrate de eliminar el archivo temporal
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except OSError as e:
                    self.instance_id._log(f"Error al eliminar el archivo temporal: {str(e)}", 'error')

    def export_to_mercado_libre(self):
        self.ensure_one()

        # Log de todos los datos del record
        record_data = {field: getattr(self, field) for field in self._fields}
        self.instance_id._log(f"Datos del producto creado: {json.dumps(record_data, default=str, indent=2)}", 'info')

        # Subir la imagen y obtener el objeto de respuesta
        upload_response_data = self.upload_image_to_mercado_libre()

        # Extrae el URL de la primera variación de imagen
        picture_url = upload_response_data['variations'][0]['secure_url']

        # Extrae los atributos requeridos desde `valid_product_template_attribute_line_ids`
        attributes = []
        for line in self.valid_product_template_attribute_line_ids:
            if line.meli_required:
                for value in line.value_ids:
                    attributes.append({
                        "id": line.attribute_id.meli_attribute_id,  # Usar el meli_attribute_id
                        "value_name": value.name
                    })

        # Prepara el payload para enviar el producto a Mercado Libre
        payload = json.dumps({
            "title": self.name,
            "category_id": self.meli_categ_id.meli_category_id,
            "price": self.list_price,
            "currency_id": self.instance_id.meli_default_currency,
            "available_quantity": self.qty_available,
            "buying_mode": "buy_it_now",
            "condition": "new",
            "listing_type_id": "gold_special",
            "pictures": [
                {
                    "source": picture_url
                }
            ],
            "attributes": attributes
        })

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {self.instance_id.meli_access_token}"
        }

        # Registro de la información de payload para debug
        self.instance_id._log(f"Exportando producto a Mercado Libre: {payload}", 'info')

        try:
            # Envía el producto a Mercado Libre
            response = requests.post("https://api.mercadolibre.com/items", headers=headers, data=payload)
            response_data = response.json()

            # Registro de la respuesta para debug
            self.instance_id._log(f"Respuesta de Mercado Libre: {response.status_code} - {response_data}", 'info')

            if response.status_code in [200, 201]:  # Considerar tanto 200 como 201 como exitosos
                item_id = response_data.get('id')
                self.default_code = item_id
                self.meli_id = item_id
                self.instance_id._log(f"Producto creado exitosamente. Item ID: {item_id}", 'info')

            else:
                # Procesar y organizar los errores en un formato más legible
                error_messages = []
                for cause in response_data.get('cause', []):
                    attribute_reference = cause.get('references', [])[0] if cause.get('references') else 'General'
                    message = cause.get('message', 'Sin mensaje de error específico')
                    error_messages.append(f"{attribute_reference}: {message}")

                error_message = "\n".join(error_messages)
                full_error_message = f"Error al exportar el producto a Mercado Libre:\n{error_message}"
                self.instance_id._log(full_error_message, 'error')
                raise UserError(full_error_message)

        except Exception as e:
            error_message = f"Excepción durante la exportación a Mercado Libre: {str(e)}"
            self.instance_id._log(error_message, 'error')
            raise UserError(error_message)

    def link_image_to_item(self, item_id, picture_id):
        self.instance_id._log(f"Vinculando imagen {picture_id} al artículo {item_id}", 'info')
        
        url = f'https://api.mercadolibre.com/items/{item_id}/pictures'
        headers = {
            'Authorization': f'Bearer {self.instance_id.meli_access_token}',
            'Content-Type': 'application/json'
        }
        payload = json.dumps({
            "id": picture_id
        })
        
        try:
            response = requests.post(url, headers=headers, data=payload)
            response_data = response.json()
            
            if response.status_code == 200:
                self.instance_id._log(f"Imagen vinculada exitosamente al artículo {item_id}", 'info')
            else:
                error_message = f"Error al vincular la imagen al artículo: {response_data}"
                self.instance_id._log(error_message, 'error')
                raise UserError(error_message)
        
        except Exception as e:
            error_message = f"Excepción durante la vinculación de la imagen al artículo: {str(e)}"
            self.instance_id._log(error_message, 'error')
            raise UserError(error_message)
    
    @api.onchange('name', 'instance_id')
    def _onchange_name(self):
        if self.name and self.instance_id:
            self._predict_category_and_set()

    def _predict_category_and_set(self, suggest_category = None):
        """Consulta el predictor de categoría de Mercado Libre y asigna la categoría sugerida al producto."""
        instance = self.instance_id
        if not instance:
            return
        if suggest_category:
            category_id = self._predict_category(instance, suggest_category)
        else:
            category_id = self._predict_category(instance, self.name)

        if category_id:
            self.meli_categ_id = category_id  # Usar el campo categ_id existente
    
    def _predict_category(self, instance, product_name):
        """Consulta el predictor de categoría de Mercado Libre y devuelve el ID de la categoría."""
        url = f"https://api.mercadolibre.com/sites/{instance.perfil_site_id}/domain_discovery/search?q={product_name}"
        headers = {
            'Authorization': f'Bearer {instance.meli_access_token}'
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            categories = response.json()
        except requests.RequestException as e:
            instance._log(f"Error al predecir categoría: {str(e)}", level='error')
            return None

        if not categories:
            instance._log("No se encontraron categorías sugeridas para este producto.", level='warning')
            return None

        # Usar la primera categoría sugerida
        category_info = categories[0]
        category_id = category_info.get('category_id')

        # Verificar si la categoría ya existe en Odoo
        existing_category = self.env['product.category'].search([('meli_category_id', '=', category_id)], limit=1)
        if existing_category:
            return existing_category.id

        # Si no existe, importar la categoría y retornar su ID
        new_category_id = instance.import_category_recursive_v2(category_id)
        return new_category_id
    
    def create_and_assign_attributes(self):
        """Crea o actualiza los atributos correspondientes a la categoría seleccionada y los asigna al producto."""
        instance = self.instance_id
        if not instance:
            raise UserError("No se encontró una instancia vinculada.")

        instance._log(f"Iniciando la asignación de atributos para el producto {self.name}", level='info')

        category_id = self.meli_categ_id.meli_category_id
        if not category_id:
            instance._log("La categoría seleccionada no tiene un ID de categoría de Mercado Libre vinculado.", level='error')
            raise UserError("La categoría seleccionada no tiene un ID de categoría de Mercado Libre vinculado.")

        instance._log(f"ID de categoría de Mercado Libre: {category_id}", level='info')

        # Consultar los atributos de la categoría en Mercado Libre
        attributes = self._fetch_category_attributes(instance, category_id)
        if not attributes:
            instance._log("No se encontraron atributos para la categoría seleccionada.", level='error')
            raise UserError("No se encontraron atributos para la categoría seleccionada.")

        instance._log(f"Atributos obtenidos: {attributes}", level='info')

        attribute_lines = []
        for attribute in attributes:
            is_required = attribute.get('tags', {}).get('required', False)
            value_type = attribute.get('value_type', 'string')  # Default to 'string' if value_type is not specified
            display_type = self._get_display_type_for_value_type(value_type)  # Determinar el display_type
            instance._log(f"Procesando atributo: {attribute['name']}, es requerido: {is_required}, tipo: {value_type}", level='info')

            # Buscar o crear el atributo
            existing_attr = self.env['product.attribute'].search([('meli_attribute_id', '=', attribute['id'])], limit=1)
            if not existing_attr:
                existing_attr = self.env['product.attribute'].create({
                    'name': attribute['name'],
                    'meli_attribute_id': attribute['id'],
                    'create_variant': 'no_variant',  # Configurar según tus necesidades
                    'display_type': display_type  # Configurar el display_type basado en value_type
                })
                instance._log(f"Atributo creado: {existing_attr.name} con display_type: {display_type}", level='info')
            else:
                instance._log(f"Atributo existente: {existing_attr.name}", level='info')

            # Buscar o crear el valor del atributo (si aplica)
            value_ids = []
            for value in attribute.get('values', []):
                existing_value = self.env['product.attribute.value'].search([
                    ('attribute_id', '=', existing_attr.id),
                    ('name', '=', value['name'])
                ], limit=1)
                if not existing_value:
                    existing_value = self.env['product.attribute.value'].create({
                        'name': value['name'],
                        'attribute_id': existing_attr.id
                    })
                    instance._log(f"Valor de atributo creado: {existing_value.name}", level='info')
                else:
                    instance._log(f"Valor de atributo existente: {existing_value.name}", level='info')
                value_ids.append(existing_value.id)

            # Si no se encuentran valores, asignar un valor por defecto según el tipo de atributo
            if not value_ids:
                default_value = self._get_default_value_for_type(value_type)
                instance._log(f"No se encontraron valores para el atributo '{attribute['name']}', asignando valor por defecto: {default_value}", level='info')

                # Crear o buscar el valor por defecto
                existing_default_value = self.env['product.attribute.value'].search([
                    ('attribute_id', '=', existing_attr.id),
                    ('name', '=', default_value)
                ], limit=1)
                if not existing_default_value:
                    existing_default_value = self.env['product.attribute.value'].create({
                        'name': default_value,
                        'attribute_id': existing_attr.id
                    })
                    instance._log(f"Valor por defecto creado: {existing_default_value.name}", level='info')
                value_ids.append(existing_default_value.id)

            # Si el atributo es requerido y no tiene valores, lanzar un error
            if is_required and not value_ids:
                instance._log(f"El atributo {attribute['name']} es requerido pero no tiene valores asignados.", level='error')
                raise UserError(f"El atributo '{attribute['name']}' es requerido pero no tiene valores disponibles para asignar.")

            attribute_lines.append((0, 0, {
                'attribute_id': existing_attr.id,
                'value_ids': [(6, 0, value_ids)] if value_ids else [],
                'meli_required': is_required,
            }))

        try:
            if attribute_lines:
                instance._log(f"Attributes: {attribute_lines}", level='info')
                instance._log(f"Asignando líneas de atributos al producto {self.name}.", level='info')
                self.attribute_line_ids = [(5, 0, 0)] + attribute_lines
        except Exception as e:
            instance._log(f"Error al asignar líneas de atributos al producto {self.name}: {str(e)}", level='error')
            raise UserError(f"Hubo un problema al asignar los atributos al producto {self.name}. Error: {str(e)}")
        
    def assign_existing_attributes(self, attributes):
        """Asignar atributos ya existentes en Mercado Libre al producto."""
        instance = self.instance_id
        if not instance:
            raise UserError("No se encontró una instancia vinculada.")

        instance._log(f"Iniciando la asignación de atributos existentes para el producto {self.name}", level='info')

        attribute_lines = []
        for attribute in attributes:
            value_type = attribute.get('value_type', 'string')  # Default to 'string' if value_type is not specified
            display_type = self._get_display_type_for_value_type(value_type)  # Determinar el display_type

            instance._log(f"Procesando atributo: {attribute['name']}, tipo: {value_type}", level='info')

            # Buscar o crear el atributo
            existing_attr = self.env['product.attribute'].search([('meli_attribute_id', '=', attribute['id'])], limit=1)
            if not existing_attr:
                existing_attr = self.env['product.attribute'].create({
                    'name': attribute['name'],
                    'meli_attribute_id': attribute['id'],
                    'create_variant': 'no_variant',  # Configurar según tus necesidades
                    'display_type': display_type  # Configurar el display_type basado en value_type
                })
                instance._log(f"Atributo creado: {existing_attr.name} con display_type: {display_type}", level='info')
            else:
                instance._log(f"Atributo existente: {existing_attr.name}", level='info')

            # Buscar o crear los valores del atributo (si aplica)
            value_ids = []
            value_id = attribute.get('value_id')
            value_name = attribute.get('value_name')

            if value_id and value_name:
                # Si value_id y value_name están presentes, buscar o crear el valor
                existing_value = self.env['product.attribute.value'].search([
                    ('attribute_id', '=', existing_attr.id),
                    ('meli_value_id', '=', value_id)
                ], limit=1)

                if not existing_value:
                    existing_value = self.env['product.attribute.value'].create({
                        'name': value_name,
                        'attribute_id': existing_attr.id,
                        'meli_value_id': value_id
                    })
                    instance._log(f"Valor de atributo creado: {existing_value.name}", level='info')
                else:
                    instance._log(f"Valor de atributo existente: {existing_value.name}", level='info')

                value_ids.append(existing_value.id)
            else:
                # Si no hay value_id, iterar sobre los posibles valores en 'values'
                for value in attribute.get('values', []):
                    existing_value = self.env['product.attribute.value'].search([
                        ('attribute_id', '=', existing_attr.id),
                        ('meli_value_id', '=', value['id'])
                    ], limit=1)

                    if not existing_value:
                        existing_value = self.env['product.attribute.value'].create({
                            'name': value['name'],
                            'attribute_id': existing_attr.id,
                            'meli_value_id': value['id']
                        })
                        instance._log(f"Valor de atributo creado: {existing_value.name}", level='info')
                    else:
                        instance._log(f"Valor de atributo existente: {existing_value.name}", level='info')

                    value_ids.append(existing_value.id)

            # Si el atributo no tiene un valor, lanzar un error
            if not value_ids:
                instance._log(f"El atributo {attribute['name']} no tiene valores asignados.", level='error')
                raise UserError(f"El atributo '{attribute['name']}' no tiene valores disponibles para asignar.")

            # Agregar la línea de atributo
            attribute_lines.append((0, 0, {
                'attribute_id': existing_attr.id,
                'value_ids': [(6, 0, value_ids)] if value_ids else [],
                'meli_required': False,  # Puedes ajustar esto si es necesario
            }))

        # Asignar los atributos al producto
        try:
            if attribute_lines:
                instance._log(f"Asignando líneas de atributos al producto {self.name}.", level='info')
                self.attribute_line_ids = [(5, 0, 0)] + attribute_lines
        except Exception as e:
            instance._log(f"Error al asignar líneas de atributos al producto {self.name}: {str(e)}", level='error')
            raise UserError(f"Hubo un problema al asignar los atributos al producto {self.name}. Error: {str(e)}")

    def _fetch_category_attributes(self, instance, category_id):
        """Consulta la API de Mercado Libre para obtener los atributos de una categoría."""
        url = f"https://api.mercadolibre.com/categories/{category_id}/attributes"
        headers = {
            'Authorization': f'Bearer {instance.meli_access_token}'
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            attributes = response.json()

            instance._log(f"Datos recibidos de la API de Mercado Libre para la categoría {category_id}: {attributes}", level='info')

            processed_attributes = []
            for attribute in attributes:
                processed_attributes.append({
                    'id': attribute['id'],
                    'name': attribute['name'],
                    'tags': attribute.get('tags', {}),
                    'values': attribute.get('values', []),
                    'value_type': attribute.get('value_type', 'string')  # Agregar el tipo de valor
                })
            instance._log(f"Atributos extraídos para la categoría {category_id}: {processed_attributes}", level='info')
            return processed_attributes
        except requests.RequestException as e:
            instance._log(f"Error al obtener atributos para la categoría '{category_id}': {str(e)}", level='error')
            return []

    def _get_default_value_for_type(self, value_type):
        """Devuelve un valor por defecto basado en el tipo de atributo."""
        defaults = {
            'string': 'Sin especificar',
            'number': '0',
            'number_unit': '0',  # La unidad no se puede predeterminar, se debe ajustar al crear valores específicos
            'boolean': 'No',  # Asumiendo que 'No' es el valor por defecto
            'list': 'No especificado'
        }
        return defaults.get(value_type, 'Sin especificar')  # Por defecto, 'Sin especificar' si el tipo no está en la lista

    def _get_display_type_for_value_type(self, value_type):
        """Devuelve el display_type de Odoo basado en el tipo de valor de Mercado Libre."""
        display_types = {
            'string': 'radio',  # Usar 'radio' por defecto para strings
            'number': 'select',  # Usar 'select' para números
            'number_unit': 'select',  # Usar 'select' para números con unidades
            'boolean': 'radio',  # Usar 'radio' para booleanos
            'list': 'pills'  # Usar 'pills' para listas
        }
        return display_types.get(value_type, 'radio')  # Por defecto, usar 'radio'
    
    def assign_tags(self, tags):
        """Asigna las etiquetas al producto, creando las etiquetas si no existen."""
        try:
            # Validar que el producto tenga una instancia asignada
            if not self.instance_id:
                raise UserError("No se ha asignado una instancia al producto.")

            # Registrar en el log de la instancia
            self.instance_id._log("Asignando etiquetas al producto", 'info')

            # Lista para almacenar los IDs de etiquetas que se van a asignar
            tag_ids = []

            # Iterar sobre las etiquetas proporcionadas
            for tag in tags:
                # Buscar si la etiqueta ya existe
                product_tag = self.env['product.tag'].search([('name', '=', tag)], limit=1)

                if not product_tag:
                    # Si la etiqueta no existe, crearla
                    product_tag = self.env['product.tag'].create({'name': tag})

                # Añadir el ID de la etiqueta a la lista
                tag_ids.append(product_tag.id)

            # Asignar las etiquetas al producto actual
            self.write({
                'product_tag_ids': [(6, 0, tag_ids)]  # Asignar las etiquetas al producto
            })

            # Registrar en el log de la instancia al finalizar
            self.instance_id._log(f"Etiquetas asignadas: {tags}", 'info')

        except UserError as ue:
            # Manejar errores específicos de usuario, como la falta de instancia
            self.instance_id._log(f"Error: {str(ue)}", 'error')
            raise ue

        except Exception as e:
            # Capturar cualquier otro error inesperado y registrarlo en el log
            error_message = f"Error inesperado al asignar etiquetas: {str(e)}"
            if self.instance_id:
                self.instance_id._log(error_message, 'error')

            raise UserError(error_message)
        
    def assign_channels(self, channels):
        """Asigna los canales al producto, creando los canales si no existen, con manejo de errores y registro de log."""
        try:
            # Validar que el producto tenga una instancia asignada
            if not self.instance_id:
                raise UserError("No se ha asignado una instancia al producto.")

            # Registrar en el log de la instancia
            self.instance_id._log("Iniciando asignación de canales al producto", 'info')

            # Lista para almacenar los IDs de canales que se van a asignar
            channel_ids = []

            # Iterar sobre los canales proporcionados
            for channel in channels:
                # Buscar si el canal ya existe
                product_channel = self.env['product.channel'].search([('name', '=', channel)], limit=1)

                if not product_channel:
                    # Si el canal no existe, crearlo
                    product_channel = self.env['product.channel'].create({'name': channel})
                    self.instance_id._log(f"Canal '{channel}' creado.", 'info')

                # Añadir el ID del canal a la lista
                channel_ids.append(product_channel.id)

            # Asignar los canales al producto actual
            self.write({
                'meli_product_channel_ids': [(6, 0, channel_ids)]  # Asignar los canales al producto
            })

            # Registrar en el log al finalizar la asignación de canales
            self.instance_id._log(f"Canales asignados: {channels}", 'info')

        except UserError as ue:
            # Manejar errores específicos de usuario, como la falta de instancia
            self.instance_id._log(f"Error de usuario: {str(ue)}", 'error')
            raise ue

        except Exception as e:
            # Capturar cualquier otro error inesperado y registrarlo en el log
            error_message = f"Error inesperado al asignar canales: {str(e)}"
            if self.instance_id:
                self.instance_id._log(error_message, 'error')
            raise UserError(error_message)

