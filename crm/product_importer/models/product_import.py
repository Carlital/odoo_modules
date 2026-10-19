import base64
import openpyxl
import requests
from odoo import models, fields, api
from odoo.exceptions import UserError
from io import BytesIO
import logging

_logger = logging.getLogger(__name__)

class ProductImport(models.TransientModel):
    _name = 'product.import'
    _description = 'Product Import'

    file = fields.Binary('File', required=True)
    filename = fields.Char('Filename')

    def import_file(self):
        if not self.file:
            raise UserError("Por favor, sube la plantilla de Excel")

        file_data = base64.b64decode(self.file)
        file_stream = BytesIO(file_data)
        wb = openpyxl.load_workbook(file_stream, data_only=True)
        sheet = wb.active

        headers = [cell.value for cell in sheet[1]]
        rows = list(sheet.iter_rows(min_row=2, values_only=True))

        required_columns = ['Product Name', 'Internal Reference', 'Image URL', 'Quantity', 'Category', 'Subcategory', 'Price', 'Description']

        # Validar encabezados requeridos en el archivo Excel
        for col in required_columns:
            if col not in headers:
                raise UserError(f"Error en la plantilla de Excel, no se encontró la columna: {col}")

        stock_location = self.env.ref('stock.stock_location_stock')  # Ubicación de stock por defecto

        for row in rows:
            row_dict = dict(zip(headers, row))

            # Validar precios y cantidades
            try:
                price_value = float(row_dict.get('Price', 0.0))
                if price_value < 0:
                    raise ValueError
            except ValueError:
                raise UserError(f"El precio del producto '{row_dict.get('Product Name')}' no es válido.")

            try:
                quantity_value = int(row_dict.get('Quantity', 0))
                if quantity_value < 0:
                    raise ValueError
            except ValueError:
                raise UserError(f"La cantidad del producto '{row_dict.get('Product Name')}' no es válida.")

            # Obtener o crear la categoría y subcategoría
            category_name = row_dict.get('Category', '').strip()
            subcategory_name = row_dict.get('Subcategory', '').strip()

            category = self.env['product.category'].search([('name', '=', category_name)], limit=1)
            if not category:
                category = self.env['product.category'].create({'name': category_name})

            subcategory = self.env['product.category'].search([('name', '=', subcategory_name), ('parent_id', '=', category.id)], limit=1)
            if not subcategory:
                subcategory = self.env['product.category'].create({'name': subcategory_name, 'parent_id': category.id})

            image_url = row_dict.get('Image URL', '').strip()
            image_data = self._get_image_from_url(image_url)
            

            # Crear o actualizar producto
            product_vals = {
                'name': row_dict.get('Product Name', ''),
                'default_code': row_dict.get('Internal Reference', ''),
                'categ_id': subcategory.id,
                'category_id': category.id,
                'subcategory_id': subcategory.id,
                'type': 'product',
                'image_url': image_url,
                'image_1920': image_data,  # Se asegura que la imagen se guarde en el campo correcto
                'list_price': price_value,
                'description_sale': row_dict.get('Description', ''),
            }

            product = self.env['product.template'].search([('default_code', '=', row_dict.get('Internal Reference'))], limit=1)
            if product:
                product.write(product_vals)
            else:
                product = self.env['product.template'].create(product_vals)

            # Manejo de stock
            quant = self.env['stock.quant'].search([
                ('product_id', '=', product.id),
                ('location_id', '=', stock_location.id)
            ], limit=1)
            if quant:
                quant.quantity = quantity_value  # Actualizar cantidad existente
            else:
                quant_vals = {
                    'product_id': product.id,
                    'location_id': stock_location.id,
                    'quantity': quantity_value,
                }
                self.env['stock.quant'].create(quant_vals)

    def _get_image_from_url(self, url):
        """Descarga una imagen desde una URL y la convierte a base64"""
        if not url:
            _logger.warning("No se proporcionó una URL de imagen.")
            return None

        # 🔹 Transformar enlaces de Google Drive
        if "drive.google.com" in url and "/file/d/" in url:
            file_id = url.split("/file/d/")[1].split("/")[0]
            url = f"https://drive.google.com/uc?export=download&id={file_id}"
            _logger.info(f"Transformando URL de Google Drive a: {url}")

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                _logger.info(f"Imagen descargada correctamente desde {url}")
                return base64.b64encode(response.content)  # 🔹 Codificamos correctamente la imagen
            else:
                _logger.error(f"Error al descargar la imagen desde la URL: {url} - Código {response.status_code}")
                raise UserError(f"No se pudo descargar la imagen. Código de error: {response.status_code}")
        except requests.RequestException as e:
            _logger.error(f"No se pudo acceder a la imagen en la URL {url}. Error: {str(e)}")
            raise UserError(f"No se pudo acceder a la imagen en la URL: {url}")
