from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import logging
import json
import base64
import re
import html
from io import BytesIO
from PIL import Image, ImageChops

try:
    LANCZOS = Image.Resampling.LANCZOS  # Pillow >=10
except Exception:
    LANCZOS = Image.LANCZOS             # Pillow <10

_logger = logging.getLogger(__name__)

class VexPublishProductWizard(models.TransientModel):
    _name = 'vex.publish.product.wizard'
    _description = 'Publicar producto en MercadoLibre'

    # Información del producto
    product_id = fields.Many2one(
        "product.template", 
        string="Producto", 
        required=True
    )
    name = fields.Char(string="Nombre")
    image_1920 = fields.Binary(string="Imagen")
    meli_thumbnail = fields.Char(
        string="Miniatura (URL)", 
        help="URL de la miniatura del producto", 
        required=True
    )
    instance_id = fields.Many2one(
        "vex.instance", 
        string="Instancia", 
        required=True
    )

    # Campos requeridos por la API
    meli_title = fields.Char(string="Título", required=True)
    meli_category_vex = fields.Char(
        string="ID Categoría ML"
    )
    meli_category_id = fields.Many2one(
        'product.category',
        string="Categoría MercadoLibre",
        required=True
    )
    last_populated_category_id = fields.Many2one(
        'product.category',
        string='Última categoría usada para poblar',
        readonly=True
    )
    
    meli_currency = fields.Selection([
        ('CLP', 'Peso Chileno (CLP)'),
        ('USD', 'Dólar Americano (USD)'),
    ], default='CLP', string="Moneda", required=True)
    meli_available_quantity = fields.Integer(string="Cantidad disponible", required=True)
    meli_buying_mode = fields.Selection(
        [
            ('buy_it_now', 'Compra inmediata'),
        ],
        string="Modo de compra",
        required=True,
        help="Modo de compra permitido por Mercado Libre"
    )
    meli_condition = fields.Selection(
        [
            ('new', 'Nuevo'),
            ('used', 'Usado'),
            ('not_specified', 'No especificado'),
        ],
        string="Condición",
        required=True,
        help="Condición del ítem para Mercado Libre"
    )
    meli_listing_type = fields.Selection(
        [
            ('gold_pro', 'Premium'),
            ('gold_special', 'Clásica'),
        ],
        string="Tipo de publicación",
        required=True,
        help="Tipo de publicación en Mercado Libre"
    )
    fixed_fee = fields.Float(string="Comisión de ML", help="Comisión fija de MercadoLibre")
    percentaje_fee = fields.Float(string="Porcentaje de comisión", help="Porcentaje de comisión de MercadoLibre")
    gross_amount = fields.Float(string="Detalle de comisión", help="Monto total de comisión de MercadoLibre")
    sale_fee_amount = fields.Float(string="Precio con comisión ML")
    meli_base_price = fields.Float(string="Precio del Producto", help="Precio original del producto")
    public_price = fields.Float(
        string="Precio a Publicar",
        help="Copia del precio antes de marcar 'Absorver Comisión'. Se usa para restaurar al desmarcar."
    )

    # Garantía
    meli_warranty_type = fields.Selection(
        [
            ('2230280', 'Garantía de Proveedor'),
            ('2230279', 'Sin garantía'),
            ('2230582', 'Garantía de fábrica'),
        ],
        string="Tipo de Garantía",
        required=True,
        default="2230280",
        help="Tipo de garantía según Mercado Libre"
    )
    meli_warranty_time = fields.Char(string="Tiempo de garantía", required=True)

    # Descripción
    meli_description = fields.Text(string="Descripción", required=True)

    # Logística
    meli_logistic_type = fields.Selection([
        ("fulfillment", "Fulfillment (Mercado Libre Full)"),
        ("cross_docking", "Cross Docking"),
        ("drop_off", "Drop Off (Sucursal de correo)"),
        ("xd_drop_off", "Cross Docking + Drop Off"),
        ("self_service", "Self Service (Logística propia)"),
        ("not_specified", "No especificado"),
    ],
        default="not_specified",
        string="Tipo de logística",
        required=True,
        help="""
        fulfillment: El producto está en los almacenes de Mercado Libre (Full).
        cross_docking: El vendedor lleva la mercadería a una estación de Mercado Libre y desde ahí se despacha.
        drop_off: El vendedor despacha el producto en una sucursal de correo autorizado por ML.
        xd_drop_off: Variante mixta: drop off + cross docking.
        self_service: El vendedor organiza y paga su propia logística.
        not_specified: No se especifica ningún tipo de logística.
        """
    )

    # Relaciones
    meli_pictures_ids = fields.One2many(
        "vex.publish.product.wizard.image", 
        "wizard_id", 
        string="Imágenes", 
        required=False
    )
    meli_attribute_ids = fields.One2many(
        "vex.publish.product.wizard.attribute", 
        "wizard_id", 
        string="Atributos", 
        required=False
    )
    absorb_price = fields.Boolean(
        string="Absorber Comisión",
        default=False,
        help="Si se marca, el precio base se ajusta para que el precio público final (incluyendo comisiones) sea igual al precio de lista del producto."
    )

    @api.onchange('product_id')
    def _onchange_product_id_set_category(self):
        for w in self:
            if w.product_id and not w.meli_category_id:
                w.meli_category_id = w.product_id.meli_category_id
            elif not w.product_id:
                w.meli_category_id = False

    # @api.onchange('meli_category_id')
    # def _onchange_meli_category_id(self):
    #     for w in self:
    #         # Sincroniza ID ML siempre
    #         w.meli_category_vex = w.meli_category_id.meli_category_id if w.meli_category_id else False

    #         # Si no hay categoría, limpia atributos
    #         if not w.meli_category_id:
    #             w.meli_attribute_ids = [(5, 0, 0)]
    #             w.last_populated_category_id = False
    #             continue

    #         # Si la categoría NO cambió realmente, NO repobles
    #         if w.last_populated_category_id and (w.last_populated_category_id == w.meli_category_id):
    #             continue

    #         # Si ya hay atributos, NO repobles (solo la primera vez)
    #         if w.meli_attribute_ids:
    #             w.last_populated_category_id = w.meli_category_id
    #             continue

    #         # Repoblar SOLO si no hay atributos
    #         atributos = []
    #         for attr in w.meli_category_id.meli_attribute_ids.filtered('meli_attribute_required'):
    #             line_vals = {
    #                 'meli_attribute_ref_id': attr.id,
    #                 'meli_attribute_name': attr.meli_attribute_name,
    #             }
    #             atributos.append((0, 0, line_vals))

    #         w.meli_attribute_ids = [(5, 0, 0)] + atributos
    #         w.last_populated_category_id = w.meli_category_id     

    @api.onchange('absorb_price')
    def _onchange_absorb_price(self):
        for w in self:
            if w.absorb_price:
                w.public_price = w.sale_fee_amount or w.meli_base_price
            else:
                w.public_price = w.meli_base_price

    @api.model
    def set_odoo_image_url_as_thumbnail(self, product):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        image_url = f"{base_url}/web/image/product.template/{product.id}/image_1920"
        product.meli_thumbnail = image_url

    @api.model
    def _copy_product_attrs_to_wizard_cmds(self, product):
        """Convierte product.meli_attribute_ids en comandos (0,0,vals) para el wizard."""
        cmds = []
        for pa in product.meli_attribute_ids:
            cmds.append((0, 0, {
                'meli_attribute_ref_id': pa.meli_attribute_ref_id.id,
                'meli_attribute_name': pa.meli_attribute_name,
                'meli_values_id': pa.meli_values_id.id if pa.meli_values_id else False,
                'meli_value_name': pa.meli_value_name,
            }))
        return cmds

    @api.onchange('meli_logistic_type', 'instance_id', 'product_id')
    def _onchange_meli_logistic_type(self):
        for wizard in self:
            qty = 0
            instance = wizard.instance_id
            product = wizard.product_id
            location = False
            if instance and product:
                if wizard.meli_logistic_type == 'fulfillment':
                    location = instance.ml_full_location_id
                else:
                    location = instance.ml_not_full_location_id
                if location:
                    quants = self.env['stock.quant'].search([
                        ('product_id', 'in', product.product_variant_ids.ids),
                        ('location_id', '=', location.id)
                    ])
                    qty = sum(quants.mapped('quantity'))
            wizard.meli_available_quantity = qty
            _logger.info(f"Logistic Type: {wizard.meli_logistic_type} | Location: {location.display_name if location else 'N/A'} | Qty: {qty}")

    # @api.onchange('meli_base_price', 'meli_category_vex')
    # def _onchange_meli_base_price_or_category(self):
    #     for wizard in self:
    #         price = wizard.meli_base_price
    #         category = wizard.meli_category_vex
    #         instance = wizard.instance_id
    #         if price and category and instance:
    #             try:
    #                 instance.get_access_token()
    #                 headers = {"Authorization": f"Bearer {instance.meli_access_token}"}
    #                 url = f"https://api.mercadolibre.com/sites/MLC/listing_prices?price={int(price)}&category_id={category}"
    #                 response = requests.get(url, headers=headers)
    #                 if response.status_code == 200:
    #                     data = response.json()
    #                     if data and isinstance(data, list):
    #                         info = data[0]
    #                         wizard.percentaje_fee = info.get('sale_fee_details', {}).get('percentage_fee', 0)
    #                         wizard.fixed_fee = info.get('sale_fee_details', {}).get('fixed_fee', 0)
    #                         wizard.gross_amount = info.get('sale_fee_details', {}).get('gross_amount', 0)
    #                 else:
    #                     _logger.warning(f"Error ML listing_prices: {response.status_code} - {response.text}")
    #             except Exception as e:
    #                 _logger.error(f"Error ML listing_prices: {e}")

    def _is_processing_placeholder(self, url: str) -> bool:
        return bool(url) and 'resources/frontend/statics/processing-image' in url

    def _crop_white_borders(self, img: Image.Image) -> Image.Image:
        """Recorta bordes casi blancos (evita que ML haga smartcrop y termine <500px)."""
        # Aplana alpha sobre blanco si existe
        if img.mode in ('RGBA', 'LA'):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1])
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Detecta diferencias respecto a un fondo blanco
        bg = Image.new('RGB', img.size, (255, 255, 255))
        diff = ImageChops.difference(img, bg)
        bbox = diff.getbbox()
        if bbox:
            img = img.crop(bbox)
        return img

    def _normalize_raw_image(self, raw_bytes: bytes) -> bytes | None:
        """Normaliza a: recorte de bordes blancos, mínimo 500px (uno de los lados) y máximo 1920px."""
        if not raw_bytes:
            return None
        try:
            img = Image.open(BytesIO(raw_bytes))
            # Recorta bordes blancos y aplanado de alpha
            img = self._crop_white_borders(img)

            w, h = img.size
            max_side = max(w, h)

            # Escala hacia arriba si ambos lados < 500 (deja el lado mayor en 500)
            if max_side < 500:
                scale = 500.0 / float(max_side)
                img = img.resize((int(round(w * scale)), int(round(h * scale))), LANCZOS)

            # Limita a 1920px como máximo
            w, h = img.size
            if max(w, h) > 1920:
                img.thumbnail((1920, 1920), LANCZOS)

            out = BytesIO()
            img.save(out, format='JPEG', quality=90, optimize=True)
            out.seek(0)
            return out.read()
        except Exception as e:
            _logger.error(f"Error normalizando imagen: {e}")
            return None

    def _extract_secure_from_pictures_resp(self, data):
        """Devuelve una secure_url válida desde la respuesta de imágenes de ML."""
        # La mayoría de respuestas traen un array de variations con secure_url
        variations = data.get('variations') or []
        if isinstance(variations, list) and variations:
            for v in variations:
                if v.get('secure_url'):
                    return v['secure_url']
        # Fallback poco frecuente
        return data.get('secure_url')

    def _is_ml_hosted(self, url: str) -> bool:
        return bool(url) and ('mlstatic.com' in url or '/pictures/' in url)

    def _upload_via_source(self, url, instance):
        """Intenta que ML ‘tire’ de la URL. Útil si ya es pública."""
        try:
            resp = requests.post(
                "https://api.mercadolibre.com/pictures",
                headers={
                    "Authorization": f"Bearer {instance.meli_access_token}",
                    "Content-Type": "application/json",
                },
                json={"source": url},
                timeout=30
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                secure = self._extract_secure_from_pictures_resp(data)
                if not secure:
                    _logger.warning(f"[pictures source] Sin secure_url en resp: {data}")
                return secure
            _logger.warning(f"[pictures source] {resp.status_code} - {resp.text}")
        except Exception as e:
            _logger.error(f"[pictures source] Exception: {e}")
        return None

    def _upload_binary(self, image_bytes, instance, filename="image.jpg", mimetype="image/jpeg"):
        try:
            files = {'file': (filename, image_bytes, mimetype)}
            resp = requests.post(
                "https://api.mercadolibre.com/pictures/items/upload",
                headers={"Authorization": f"Bearer {instance.meli_access_token}"},
                files=files,
                timeout=60
            )
            if resp.status_code in (200, 201):
                return self._extract_secure_from_pictures_resp(resp.json())
            _logger.warning(f"[items/upload] {resp.status_code} - {resp.text}")
        except Exception as e:
            _logger.error(f"[items/upload] Exception: {e}")
        return None

    def _image_bytes_from_b64(self, b64_data):
        if not b64_data:
            return None
        try:
            raw = base64.b64decode(b64_data)
            return self._normalize_raw_image(raw)  # <- usa la normalización (recorte + min 500 + max 1920)
        except Exception as e:
            _logger.error(f"Error procesando imagen base64: {e}")
            return None
        
    def _prepare_plain_description(self, text: str) -> str:
        """Normaliza la descripción a texto plano respetando saltos y viñetas."""
        if not text:
            return ''
        # Decodifica entidades HTML por si vienen desde description_sale
        text = html.unescape(text)

        # Sustituye tags por saltos y elimina el resto
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.I)
        text = re.sub(r'</(p|li|div|h[1-6])\s*>', '\n', text, flags=re.I)
        text = re.sub(r'<(ul|ol)\b[^>]*>', '\n', text, flags=re.I)
        text = re.sub(r'<[^>]+>', ' ', text)  # quita cualquier otra etiqueta

        # Normaliza saltos
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # Recorta espacios por línea pero conserva líneas vacías
        lines = [ln.strip() for ln in text.split('\n')]
        text = '\n'.join(lines)

        # Colapsa 3+ saltos en solo 2 (mantiene separación de párrafos)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Recorta espacios múltiples
        text = re.sub(r'[ \t]{2,}', ' ', text).strip()

        # Límite de seguridad
        return text[:50000]

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        product = self.env['product.template'].browse(self.env.context.get('active_id'))

        res['product_id'] = product.id
        res['meli_category_id'] = product.meli_category_id.id if product.meli_category_id else False
        res['meli_category_vex'] = product.meli_category_id.meli_category_id if product.meli_category_id else False
        res['last_populated_category_id'] = product.meli_category_id.id if product.meli_category_id else False
        res['name'] = product.name
        res['image_1920'] = product.image_1920
        res['meli_title'] = product.name

        # --- Generar URL imagen principal ---
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        variant = product.product_variant_id
        res['meli_thumbnail'] = f"{base_url}/web/image/product.product/{variant.id}/image_1920"

        # --- Copiar campos simples ---
        for field in [
            'meli_buying_mode',
            'meli_condition', 'meli_listing_type',
            'meli_warranty_time', 'meli_warranty_type',
        ]:
            res[field] = getattr(product, field)

        res['meli_base_price'] = product.list_price
        res['meli_base_price_snapshot'] = res.get('meli_base_price', 0.0)
        res['meli_description'] = product.description_sale

        # --- Calcular gross_amount con API de ML ---
        price = product.list_price
        ml_category_id = product.meli_category_id.meli_category_id if product.meli_category_id else None
        instance = product.instance_id or self.env['vex.instance'].search([('name', 'ilike', 'RIFCIF ODOO')], limit=1)
        if instance:
            res['instance_id'] = instance.id
        if price and ml_category_id:
            try:
                instance.get_access_token()
                url = f"https://api.mercadolibre.com/sites/MLC/listing_prices?price={int(price)}&category_id={ml_category_id}"
                headers = {"Authorization": f"Bearer {instance.meli_access_token}"}
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if data and isinstance(data, list):
                        info = data[0]
                        res['fixed_fee'] = info.get('sale_fee_details', {}).get('fixed_fee', 0)
                        res['percentaje_fee'] = info.get('sale_fee_details', {}).get('percentage_fee', 0)
                        res['gross_amount'] = info.get('sale_fee_details', {}).get('gross_amount', 0)
                        res['sale_fee_amount'] = info.get('sale_fee_amount', 0.0)
                        res['meli_base_price'] = price
                        res['public_price'] = price
                        _logger.info(f"[default_get] API ML precios: {info}")
                    else:
                        _logger.warning("[default_get] Respuesta vacía o inesperada de la API de Mercado Libre.")
                else:
                    _logger.warning(f"[default_get] Error al consultar la API de ML: {response.status_code} - {response.text}")
            except Exception as e:
                _logger.error(f"[default_get] Error al consumir la API de ML: {e}")

        # --- Imágenes secundarias ---
        pictures = [
            (0, 0, {'url': img.url, 'secure_url': img.secure_url})
            for img in product.meli_pictures_ids
            if img.secure_url != product.meli_thumbnail
        ]
        res['meli_pictures_ids'] = pictures

        # --- Atributos para el wizard ---
        if product.meli_attribute_ids:
            res['meli_attribute_ids'] = self._copy_product_attrs_to_wizard_cmds(product)
        else:
            odoo_category = product.meli_category_id
            if odoo_category:
                atributos = []
                for attr in odoo_category.meli_attribute_ids.filtered(lambda a: a.meli_attribute_required):
                    atributos.append((0, 0, {
                        'meli_attribute_ref_id': attr.id,
                        'meli_attribute_name': attr.meli_attribute_name,
                        'meli_values_id': attr.value_ids.id if len(attr.value_ids) == 1 else False,
                    }))
                res['meli_attribute_ids'] = atributos
            
        # --- Instancia por defecto ---
        instance = self.env['vex.instance'].search([('name', 'ilike', 'RIFCIF ODOO')], limit=1)
        if instance:
            res['instance_id'] = instance.id

        # --- Definir tipo logístico por defecto ---
        logistic_type = res.get('meli_logistic_type') or 'not_specified'
        res['meli_logistic_type'] = logistic_type

        return res

    def action_publish(self):
        self.ensure_one()
        _logger.info(f"=== Iniciando publicación del producto {self.product_id.name} (ID {self.product_id.id}) ===")

        # --- TOKEN (necesario antes de subir imágenes) ---
        instance = self.instance_id
        access_token = instance.meli_access_token
        if not access_token or len(access_token) < 20:
            raise UserError("Token de acceso no válido.")
        _logger.info(f"Access Token usado: {access_token[:10]}... (ocultado por seguridad)")

        # --- ARMAR IMÁGENES (robusto) ---
        pictures = []

        # 1) Principal
        main_bytes = self._image_bytes_from_b64(self.product_id.image_1920 or self.product_id.product_variant_id.image_1920)
        secure = None
        if main_bytes:
            secure = self._upload_binary(main_bytes, self.instance_id, filename=f"{self.product_id.id}.jpg")
            if secure and self._is_processing_placeholder(secure):
                _logger.warning("ML devolvió placeholder para la imagen principal; se intentará fallback.")
                secure = None
        else:
            _logger.warning("Sin binario image_1920; probando con URL del thumbnail.")

        # Fallback por URL
        if not secure:
            thumb = (self.meli_thumbnail or "").strip()
            if thumb:
                if self._is_ml_hosted(thumb) and not self._is_processing_placeholder(thumb):
                    secure = thumb
                else:
                    secure = self._upload_via_source(thumb, self.instance_id)
                    if secure and self._is_processing_placeholder(secure):
                        _logger.warning("ML devolvió placeholder desde source; intentaremos descarga+multipart.")
                        secure = None
                    if not secure:
                        try:
                            r = requests.get(thumb, timeout=20)
                            if r.status_code == 200 and r.content:
                                norm = self._normalize_raw_image(r.content)
                                secure = self._upload_binary(norm, self.instance_id, filename="main.jpg") if norm else None
                            else:
                                _logger.warning(f"No se pudo descargar thumbnail {thumb}: {r.status_code}")
                        except Exception as e:
                            _logger.error(f"Error descargando thumbnail {thumb}: {e}")

        if secure:
            pictures.append({"source": secure})

        # 2) Secundarias
        for pic in self.meli_pictures_ids:
            src = (pic.secure_url or pic.url or "").strip()
            if not src:
                continue
            if self._is_ml_hosted(src) and not self._is_processing_placeholder(src):
                pictures.append({"source": src})
                continue

            sec_secure = self._upload_via_source(src, self.instance_id)
            if sec_secure and self._is_processing_placeholder(sec_secure):
                sec_secure = None
            if not sec_secure:
                try:
                    r = requests.get(src, timeout=20)
                    if r.status_code == 200 and r.content:
                        norm = self._normalize_raw_image(r.content)
                        sec_secure = self._upload_binary(norm, self.instance_id, filename="extra.jpg") if norm else None
                    else:
                        _logger.warning(f"No se pudo descargar {src}: {r.status_code}")
                except Exception as e:
                    _logger.error(f"Error descargando {src}: {e}")

            if sec_secure and not self._is_processing_placeholder(sec_secure):
                pictures.append({"source": sec_secure})

        if not pictures:
            raise UserError("Debes agregar al menos una imagen válida para publicar en MercadoLibre. No fue posible subir ni reutilizar ninguna imagen. Revisa que las URLs sean públicas o que el producto tenga image_1920.")
        # Quitar duplicados
        seen, unique = set(), []
        for p in pictures:
            src = p.get('source')
            if src and src not in seen:
                seen.add(src)
                unique.append(p)
        pictures = unique
        _logger.info(f"Total imágenes preparadas para ML: {len(pictures)}")

        # --- ATRIBUTOS (tomados del wizard) ---
        attributes = []
        for attr in self.meli_attribute_ids:
            attribute_id = attr.meli_attribute_ref_id.meli_attribute_id
            value_id = attr.meli_values_id.meli_value_id if attr.meli_values_id else None
            value_name = attr.meli_values_id.meli_value_name if attr.meli_values_id else attr.meli_value_name
            data = {"id": attribute_id}
            if value_id:
                data["value_id"] = value_id
            if value_name and not value_id:
                data["value_name"] = value_name
            attributes.append(data)
        _logger.info(f"Atributos preparados para ML: {attributes}")

        # --- TÉRMINOS DE VENTA ---
        sale_terms = []
        if self.meli_warranty_type:
            sale_terms.append({"id": "WARRANTY_TYPE", "value_id": self.meli_warranty_type})
        if self.meli_warranty_time:
            sale_terms.append({"id": "WARRANTY_TIME", "value_name": self.meli_warranty_time})
        _logger.info(f"Términos de venta: {sale_terms}")

        # --- VALIDACIÓN (antes de tocar product.template) ---
        if not self.meli_category_vex or not self.meli_category_vex.startswith('ML'):
            _logger.error("Categoría inválida detectada.")
            raise UserError("Debes ingresar un ID de categoría válido de MercadoLibre, por ejemplo: MLA1055.")
        missing = [a for a in self.meli_attribute_ids if a.meli_attribute_ref_id.meli_attribute_required and not (a.meli_values_id or a.meli_value_name)]
        if missing:
            raise UserError("Faltan valores para algunos atributos requeridos.")

        # --- PAYLOAD ---
        payload = {
            "title": self.meli_title,
            "category_id": self.meli_category_vex,
            "currency_id": self.meli_currency,
            "available_quantity": self.meli_available_quantity,
            "buying_mode": self.meli_buying_mode,
            "condition": self.meli_condition,
            "listing_type_id": self.meli_listing_type,
            "price": int(self.meli_base_price), 
            "pictures": pictures,
            "attributes": attributes,
            "sale_terms": sale_terms,
        }
        _logger.info(f"Payload final enviado a ML: {json.dumps(payload, indent=2, ensure_ascii=False)}")

        # --- POST A MERCADO LIBRE ---
        url = "https://api.mercadolibre.com/items"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        _logger.info(f"Respuesta de Mercado Libre [{response.status_code}]: {response.text}")
        if response.status_code != 201:
            _logger.error(f"Error al crear el producto en ML: {response.text}")
            raise UserError(f"Error al crear el producto en MercadoLibre: {response.text}")

        data = response.json()
        plain_desc = self._prepare_plain_description(self.meli_description)
        if plain_desc:
            desc_endpoint = f"https://api.mercadolibre.com/items/{data.get('id')}/description"
            desc_payload = {"plain_text": plain_desc}
            desc_resp = requests.post(desc_endpoint, headers=headers, json=desc_payload)
            if desc_resp.status_code in (200, 201):
                _logger.info(f"Descripción creada correctamente para {data.get('id')}")
                # Verificar que quedó en ML
                try:
                    ver = requests.get(
                        f"https://api.mercadolibre.com/items/{data.get('id')}/description",
                        headers=headers, timeout=15
                    )
                    if ver.status_code == 200:
                        got = ver.json() or {}
                        _logger.info(f"Descripción en ML confirmada (len={len(got.get('plain_text') or '')}).")
                    else:
                        _logger.warning(f"No se pudo verificar descripción: {ver.status_code} - {ver.text}")
                except Exception as e:
                    _logger.warning(f"GET descripción falló: {e}")
            else:
                # Si ya existe, intenta PUT
                put_resp = requests.put(desc_endpoint, headers=headers, json=desc_payload)
                if put_resp.status_code in (200, 201):
                    _logger.info(f"Descripción actualizada vía PUT para {data.get('id')}")
                else:
                    _logger.warning(f"No se pudo crear/actualizar descripción: {desc_resp.status_code}/{put_resp.status_code}")

        # --- ACTUALIZAR CAMPOS SIMPLES EN product.template (solo si todo validó) ---
        vals = {
            'meli_title': self.meli_title,
            'meli_category_vex': self.meli_category_vex,
            'meli_currency_id': self.meli_currency,
            'meli_available_quantity': self.meli_available_quantity,
            'meli_buying_mode': self.meli_buying_mode,
            'meli_condition': self.meli_condition,
            'meli_listing_type': self.meli_listing_type,
            'meli_base_price': self.meli_base_price,
            'meli_warranty_type': self.meli_warranty_type,
            'meli_warranty_time': self.meli_warranty_time,
            'meli_description': self.meli_description,
            'meli_thumbnail': self.meli_thumbnail,
            'meli_logistic_type': self.meli_logistic_type,
        }
        self.product_id.write(vals)
        _logger.info(f"Campos simples sincronizados con product.template: {vals}")

        # --- SINCRONIZAR IMÁGENES SECUNDARIAS EN product.template ---
        self.product_id.meli_pictures_ids.unlink()
        _logger.info("Imágenes previas eliminadas en product.template.")
        for img in self.meli_pictures_ids:
            self.product_id.meli_pictures_ids.create({
                'product_tmpl_id': self.product_id.id,
                'url': img.url,
                'secure_url': img.secure_url,
            })
        _logger.info(f"Imágenes secundarias sincronizadas: {len(self.meli_pictures_ids)}")

        # --- SINCRONIZAR ATRIBUTOS EN product.template ---
        self.product_id.meli_attribute_ids.unlink()
        _logger.info("Atributos previos eliminados en product.template.")
        for attr in self.meli_attribute_ids:
            self.product_id.meli_attribute_ids.create({
                'product_tmpl_id': self.product_id.id,
                'meli_attribute_ref_id': attr.meli_attribute_ref_id.id,
                'meli_attribute_name': attr.meli_attribute_name,
                'meli_values_id': attr.meli_values_id.id,
                'meli_value_name': attr.meli_value_name,
            })
        _logger.info(f"Atributos sincronizados: {len(self.meli_attribute_ids)}")

        if self.meli_logistic_type == 'fulfillment':
            self.product_id.meli_stock_location_id = self.instance_id.ml_full_location_id
        else:
            self.product_id.meli_stock_location_id = self.instance_id.ml_not_full_location_id

        _logger.info(f"Bodega ML asignada en product.template: {self.product_id.meli_stock_location_id.display_name}")

        self.product_id.write({
            'meli_product_id': data.get('id'),
            'meli_site_id': data.get('site_id'),
            'meli_status': data.get('status'),
            'meli_sub_status': ','.join(data.get('sub_status', [])) if data.get('sub_status') else False,
            'meli_listing_type': data.get('listing_type_id'),
            'meli_condition': data.get('condition'),
            'meli_title': data.get('title'),
            'meli_permalink': data.get('permalink'),
            'meli_thumbnail': data.get('thumbnail'),
            'meli_domain_id': data.get('domain_id'),
            'meli_catalog_product_id': data.get('catalog_product_id'),
            'meli_category_vex': data.get('category_id'),
            'meli_inventory_id': data.get('inventory_id'),
            'meli_health': data.get('health'),
        })
        _logger.info(f"Producto publicado con éxito en ML. ID: {data.get('id')} | Status: {data.get('status')}")

        return {
            'type': 'ir.actions.act_window',
            "res_model": 'product.template',
            "view_mode": 'form',
            "res_id": self.product_id.id
        }
