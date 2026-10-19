# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

import io
import base64
import openpyxl
import xlrd
import requests

class ProductExportWizard(models.TransientModel):
    _name = 'product.export.wizard'
    _description = 'Wizard para Exportación Masiva de Productos'

    # Campo para seleccionar productos que no han sido exportados
    product_ids = fields.Many2many(
        'product.template', 
        string="Productos a Exportar", 
        domain=[('meli_id', '=', False)],  # Filtrar productos sin meli_id
        help="Seleccione los productos que desea exportar a Mercado Libre"
    )
    
    # Campo para seleccionar la instancia de Mercado Libre
    instance_id = fields.Many2one('vex.instance', string="Instancia", required=True)

    # Campo para subir un archivo Excel
    file = fields.Binary('Archivo Excel')
    file_name = fields.Char('Nombre del Archivo')
    support_drive_download = fields.Boolean(string="Support for URL Image Drive", help="Habilitar descarga de imágenes desde Google Drive.")

    
    def confirm_action(self):
        """Exportar productos seleccionados o desde Excel."""
        # Log inicial de la acción
        self.instance_id._log(f"Iniciando la exportación masiva de productos usando la instancia {self.instance_id.perfil_nickname}", level='info')

        if self.product_ids:
            self.instance_id._log("Exportando productos seleccionados.", level='info')
            self._export_selected_products()
        elif self.file:
            self.instance_id._log("Exportando productos desde el archivo Excel.", level='info')
            self._export_from_excel()
        else:
            self.instance_id._log("Error: No se seleccionaron productos ni se subió un archivo Excel.", level='error')
            raise UserError("Debe seleccionar productos o subir un archivo Excel para la exportación.")

        self.instance_id._log("Exportación masiva completada.", level='info')
        return {'type': 'ir.actions.act_window_close'}

    def _export_selected_products(self):
        """Exportar productos seleccionados a Mercado Libre."""
        for product in self.product_ids:
            try:
                self.instance_id._log(f"Exportando producto {product.name} con ID {product.id}", level='info')
                product.instance_id = self.instance_id
                product.export_to_mercado_libre()
                self.instance_id._log(f"Producto {product.name} exportado exitosamente.", level='info')
            except Exception as e:
                self.instance_id._log(f"Error al exportar el producto {product.name}: {str(e)}", level='error')

    def _export_from_excel(self):
        """Leer productos de un archivo Excel y exportarlos a Mercado Libre."""
        if not self.file:
            self.instance_id._log("Error: No se subió un archivo Excel.", level='error')
            raise UserError("Debe subir un archivo Excel.")
        
        # Decodificar el archivo Excel
        data = base64.b64decode(self.file)

        # Leer el archivo Excel con openpyxl
        try:
            book = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
            sheet = book.active
        except Exception as e:
            self.instance_id._log(f"Error al abrir el archivo Excel: {str(e)}", level='error')
            raise UserError("Error al abrir el archivo Excel.")
        
        for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):  # Saltamos la primera fila (encabezados)
            product_name = row[0]  # Primera columna: nombre del producto
            drive_image_urls = row[1]  # Segunda columna: URLs de Google Drive separadas por comas
            description = row[2] #
            regular_price = row[3] #
            discount_price = row[4] #
            category = row[5] #
            stock_status = row[6] #
            SKU = row[7] #
            comentary = row[8]
            # Validación para nombres de productos vacíos
            if not product_name:
                self.instance_id._log(f"Fila {row_idx}: El nombre del producto está vacío. Saltando esta fila.", level='warning')
                continue  # Saltar fila si el nombre del producto está vacío
            
            self.instance_id._log(f"Procesando producto del archivo Excel: {product_name}", level='info')

            # Buscar o crear el producto
            product = self.env['product.template'].search([('name', '=', product_name)], limit=1)
            if not product:
                self.instance_id._log(f"Creando nuevo producto: {product_name}", level='info')
                product = self.env['product.template'].sudo().create({
                    'name': product_name,
                    'meli_description': description,
                    'list_price': regular_price,
                    'standard_price': discount_price ,  # Precio de costo si es necesario
                    'default_code': SKU,  # Asignar el SKU
                    'instance_id': self.instance_id.id,
                    'type': 'product' # if stock_status == 'stock' else 'service',  # Asumimos que stock_status es "stock" o "service"
                })
                
            # Validación para URLs vacías
            if not drive_image_urls:
                self.instance_id._log(f"Fila {row_idx}: No se encontraron URLs de imágenes para el producto {product_name}.", level='warning')
                continue  # Saltar fila si no hay URLs

            # Descargar y asignar la primera imagen desde las URLs de Google Drive al campo `image_1920`
            image_urls_list = drive_image_urls.split(",")  # Separar las URLs por comas
            for url in image_urls_list:
                url = url.strip()
                if not url:
                    self.instance_id._log(f"Fila {row_idx}: URL de imagen vacía. Saltando URL.", level='warning')
                    continue

                try:
                    image_data = self.download_image_from_drive(url)  # Descargar la imagen desde Google Drive
                    product.image_1920 = image_data  # Asignar la imagen descargada al campo `image_1920`
                    product.image_128 = image_data 
                    
                    product._predict_category_and_set(category)
                    product.create_and_assign_attributes()
                    product.export_to_mercado_libre()
                    
                    self.instance_id._log(f"Imagen descargada y asignada desde {url} para el producto {product_name}", level='info')
                    break  # Solo necesitamos la primera imagen válida, salir del bucle
                except Exception as e:
                    self.instance_id._log(f"Error al descargar la imagen desde {url} para el producto {product_name}: {str(e)}", level='error')

            # Exportar el producto a Mercado Libre
            try:
                self.instance_id._log(f"Producto {product.name} exportado exitosamente TEST desde el archivo Excel.", level='info')
            except Exception as e:
                self.instance_id._log(f"Error al exportar el producto {product.name} desde el archivo Excel: {str(e)}", level='error')
    
    def download_image_from_drive(self, url_imagen):
        """Descargar una imagen desde una URL de Google Drive y registrar logs detallados."""
        self.instance_id._log(f"Iniciando la descarga de la imagen desde: {url_imagen}", level='info')
        
        try:
            # Extraer el file_id de la URL de Google Drive
            file_id = url_imagen.split('/d/')[1].split('/view')[0]
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            self.instance_id._log(f"Transformando la URL a formato de descarga directa: {download_url}", level='info')

            # Hacer la petición GET para descargar el archivo
            response = requests.get(download_url, timeout=10)
            response.raise_for_status()  # Lanza excepción para códigos de estado 4xx/5xx

            # Si la respuesta es exitosa, loggear el tamaño de la imagen
            image_size_kb = len(response.content) / 1024  # Tamaño de la imagen en KB
            self.instance_id._log(f"Imagen descargada con éxito desde {download_url} - Tamaño: {image_size_kb:.2f} KB", level='info')

            # Retornar el archivo en formato base64
            return base64.b64encode(response.content)
        
        except requests.exceptions.RequestException as e:
            # Log detallado de cualquier error durante la petición
            self.instance_id._log(f"Error al descargar la imagen desde {download_url}: {str(e)}", level='error')
            raise UserError(f"Error al descargar el archivo desde Google Drive: {str(e)}")

        except Exception as e:
            # Capturar cualquier otra excepción inesperada
            self.instance_id._log(f"Error inesperado al procesar la descarga: {str(e)}", level='error')
            raise UserError(f"Error inesperado: {str(e)}")
