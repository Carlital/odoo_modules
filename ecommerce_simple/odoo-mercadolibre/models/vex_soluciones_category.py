from odoo import api, fields, models, _
from odoo.exceptions import UserError
import requests
import logging
class VexProductCategory(models.Model):
    _inherit         = "product.category"

    meli_code = fields.Char('Código ML')
    server_meli = fields.Boolean('server_meli')
    instance_id = fields.Many2one('vex.instance', string='instance')
    meli_category_id = fields.Char(
        string='Meli Category ID',
        help='ID of the category in Mercado Libre',
        copy=False)
    
    # New Version 2.0 fields
    meli_picture_link = fields.Char(
        string="Picture Link",
        help="URL of the representative picture for this category."
    )
    meli_permalink = fields.Char(
        string="Permalink",
        help="Permanent URL link for this Mercado Libre category."
    )
    # Settings
    meli_adult_content = fields.Boolean(
        string="Adult Content",
        help="Indicates if the category contains adult content."
    )
    meli_buying_allowed = fields.Boolean(
        string="Buying Allowed",
        help="Indicates if buying is allowed in this category."
    )
    meli_buying_modes = fields.Char(
        string="Buying Modes",
        help="Allowed buying modes for this category (comma separated)."
    )
    meli_catalog_domain = fields.Char(
        string="Catalog Domain",
        help="Catalog domain for this category."
    )
    meli_coverage_areas = fields.Char(
        string="Coverage Areas",
        help="Coverage areas for this category."
    )
    meli_currencies = fields.Char(
        string="Currencies",
        help="Allowed currencies for this category (comma separated)."
    )
    meli_fragile = fields.Boolean(
        string="Fragile",
        help="Indicates if items in this category are fragile."
    )
    meli_immediate_payment = fields.Char(
        string="Immediate Payment",
        help="Immediate payment requirement for this category."
    )
    meli_item_conditions = fields.Char(
        string="Item Conditions",
        help="Allowed item conditions for this category (comma separated)."
    )
    meli_items_reviews_allowed = fields.Boolean(
        string="Items Reviews Allowed",
        help="Indicates if item reviews are allowed in this category."
    )
    meli_listing_allowed = fields.Boolean(
        string="Listing Allowed",
        help="Indicates if listing is allowed in this category."
    )
    meli_max_description_length = fields.Integer(
        string="Max Description Length",
        help="Maximum description length for items in this category."
    )
    meli_max_pictures_per_item = fields.Integer(
        string="Max Pictures Per Item",
        help="Maximum number of pictures per item."
    )
    meli_max_pictures_per_item_var = fields.Integer(
        string="Max Pictures Per Item Variant",
        help="Maximum number of pictures per item variant."
    )
    meli_max_sub_title_length = fields.Integer(
        string="Max Sub Title Length",
        help="Maximum subtitle length for items in this category."
    )
    meli_max_title_length = fields.Integer(
        string="Max Title Length",
        help="Maximum title length for items in this category."
    )
    meli_max_variations_allowed = fields.Integer(
        string="Max Variations Allowed",
        help="Maximum number of variations allowed for items in this category."
    )
    meli_maximum_price = fields.Float(
        string="Maximum Price",
        help="Maximum price allowed for items in this category."
    )
    meli_maximum_price_currency = fields.Char(
        string="Maximum Price Currency",
        help="Currency for the maximum price."
    )
    meli_minimum_price = fields.Float(
        string="Minimum Price",
        help="Minimum price allowed for items in this category."
    )
    meli_minimum_price_currency = fields.Char(
        string="Minimum Price Currency",
        help="Currency for the minimum price."
    )
    meli_mirror_category = fields.Char(
        string="Mirror Category",
        help="Mirror category ID."
    )
    meli_mirror_master_category = fields.Char(
        string="Mirror Master Category",
        help="Mirror master category ID."
    )
    meli_mirror_slave_categories = fields.Char(
        string="Mirror Slave Categories",
        help="Mirror slave categories (comma separated)."
    )
    meli_price = fields.Char(
        string="Price",
        help="Price requirement for this category."
    )
    meli_reservation_allowed = fields.Char(
        string="Reservation Allowed",
        help="Reservation allowed setting for this category."
    )
    meli_restrictions = fields.Char(
        string="Restrictions",
        help="Restrictions for this category (comma separated)."
    )
    meli_rounded_address = fields.Boolean(
        string="Rounded Address",
        help="Indicates if rounded address is enabled for this category."
    )
    meli_seller_contact = fields.Char(
        string="Seller Contact",
        help="Seller contact setting for this category."
    )
    meli_shipping_options = fields.Char(
        string="Shipping Options",
        help="Allowed shipping options for this category (comma separated)."
    )
    meli_shipping_profile = fields.Char(
        string="Shipping Profile",
        help="Shipping profile setting for this category."
    )
    meli_show_contact_information = fields.Boolean(
        string="Show Contact Information",
        help="Indicates if contact information is shown for this category."
    )
    meli_simple_shipping = fields.Char(
        string="Simple Shipping",
        help="Simple shipping setting for this category."
    )
    meli_stock = fields.Char(
        string="Stock",
        help="Stock requirement for this category."
    )
    meli_sub_vertical = fields.Char(
        string="Sub Vertical",
        help="Sub vertical for this category."
    )
    meli_subscribable = fields.Boolean(
        string="Subscribable",
        help="Indicates if the category is subscribable."
    )
    meli_tags = fields.Char(
        string="Tags",
        help="Tags for this category (comma separated)."
    )
    meli_vertical = fields.Char(
        string="Vertical",
        help="Vertical for this category."
    )
    meli_vip_subdomain = fields.Char(
        string="VIP Subdomain",
        help="VIP subdomain for this category."
    )
    meli_buyer_protection_programs = fields.Char(
        string="Buyer Protection Programs",
        help="Buyer protection programs for this category (comma separated)."
    )
    meli_status = fields.Char(
        string="Status",
        help="Status of this category."
    )
    instance_id = fields.Many2one('vex.instance', string='instance')
    meli_category_id = fields.Char(
        string='Meli Category ID',
        help='ID of the category in Mercado Libre',
        copy=False)

    # Campos de Atributos
    meli_attribute_ids = fields.One2many('vex.meli.attribute', 'meli_category_id', string='Atributos MercadoLibre')
    
    # Valores de Atributos
    meli_attribute_value_ids = fields.One2many(
        'vex.meli.attribute.value',
        compute='_compute_meli_attribute_value_ids',
        string='Valores de Atributos',
        store=False
    )

    meli_description = fields.Char(string="Descripcion del Atributo")

    @api.depends('meli_attribute_ids.value_ids')
    def _compute_meli_attribute_value_ids(self):
        for rec in self:
            rec.meli_attribute_value_ids = rec.meli_attribute_ids.mapped('value_ids')

    def action_get_details(self):
        """Fetches details from Mercado Libre API for the selected category."""
        instance = self.instance_id
        if not instance or not instance.meli_access_token:
            raise UserError(_("No se encontró el token de acceso en la instancia asociada."))

        url = f"https://api.mercadolibre.com/categories/{self.meli_category_id}"
        headers = {
            'Authorization': f'Bearer {instance.meli_access_token}'
        }

        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            raise UserError(_("Error al consultar la API de MercadoLibre:\n%s") % str(e))

        settings = data.get('settings', {})
        meli_root = data.get('path_from_root', [{}])
        parent_category = False
        meli_category_parent_id = False
        ml_marketplace = self.env.ref('odoo-mercadolibre.vex_marketplace_mercadolibre', raise_if_not_found=False)

        # Evitar recursión infinita y solo subir hasta la categoría raíz
        if len(meli_root) > 1:
            meli_category_parent_id = meli_root[-2].get('id')
            if meli_category_parent_id and meli_category_parent_id != self.meli_category_id:
                parent_category = self.env['product.category'].search([
                    ('meli_category_id', '=', meli_category_parent_id)
                ], limit=1)

                if not parent_category:
                    parent_category = self.env['product.category'].create({
                        'name': meli_root[-2].get('name', 'Sin nombre'),
                        'meli_category_id': meli_category_parent_id,
                        'instance_id': instance.id,
                        'marketplace_ids': [(4, ml_marketplace.id)],

                    })
                    # Solo llamar recursivamente si acabamos de crear la categoría
                    parent_category.action_get_details()

        self.write({
            'parent_id': parent_category.id if parent_category else False,
            'name': data.get('name'),
            'meli_picture_link': data.get('picture'),
            'meli_permalink': data.get('permalink'),
            'meli_adult_content': settings.get('adult_content'),
            'meli_buying_allowed': settings.get('buying_allowed'),
            'meli_buying_modes': ','.join(settings.get('buying_modes', [])),
            'meli_catalog_domain': settings.get('catalog_domain'),
            'meli_coverage_areas': settings.get('coverage_areas'),
            'meli_currencies': ','.join(settings.get('currencies', [])),
            'meli_fragile': settings.get('fragile'),
            'meli_immediate_payment': settings.get('immediate_payment'),
            'meli_item_conditions': ','.join(settings.get('item_conditions', [])),
            'meli_items_reviews_allowed': settings.get('items_reviews_allowed'),
            'meli_listing_allowed': settings.get('listing_allowed'),
            'meli_max_description_length': settings.get('max_description_length'),
            'meli_max_pictures_per_item': settings.get('max_pictures_per_item'),
            'meli_max_pictures_per_item_var': settings.get('max_pictures_per_item_var'),
            'meli_max_sub_title_length': settings.get('max_sub_title_length'),
            'meli_max_title_length': settings.get('max_title_length'),
            'meli_max_variations_allowed': settings.get('max_variations_allowed'),
            'meli_maximum_price': settings.get('maximum_price'),
            'meli_maximum_price_currency': settings.get('maximum_price_currency'),
            'meli_minimum_price': settings.get('minimum_price'),
            'meli_minimum_price_currency': settings.get('minimum_price_currency'),
            'meli_mirror_category': settings.get('mirror_category'),
            'meli_mirror_master_category': settings.get('mirror_master_category'),
            'meli_mirror_slave_categories': ','.join(settings.get('mirror_slave_categories', [])),
            'meli_price': settings.get('price'),
            'meli_reservation_allowed': settings.get('reservation_allowed'),
            'meli_restrictions': ','.join(settings.get('restrictions', [])),
            'meli_rounded_address': settings.get('rounded_address'),
            'meli_seller_contact': settings.get('seller_contact'),
            'meli_shipping_options': ','.join(settings.get('shipping_options', [])),
            'meli_shipping_profile': settings.get('shipping_profile'),
            'meli_show_contact_information': settings.get('show_contact_information'),
            'meli_simple_shipping': settings.get('simple_shipping'),
            'meli_stock': settings.get('stock'),
            'meli_sub_vertical': settings.get('sub_vertical'),
            'meli_subscribable': settings.get('subscribable'),
            'meli_tags': ','.join(settings.get('tags', [])),
            'meli_vertical': settings.get('vertical'),
            'meli_vip_subdomain': settings.get('vip_subdomain'),
            'meli_buyer_protection_programs': ','.join(settings.get('buyer_protection_programs', [])),
            'meli_status': settings.get('status'),
        })

    def action_view_attributes(self):
        self.ensure_one()
        instance = self.env['vex.instance'].search([('name', 'ilike', 'RIFCIF ODOO')], limit=1)
        if not instance:
            raise UserError("No se encontró la instancia asociada ni una instancia por defecto (RIFCIF ODOO).")

        instance.get_access_token()
        if not instance.meli_access_token:
            raise UserError("No se encontró el token de acceso en la instancia asociada.")

        url = f"https://api.mercadolibre.com/categories/{self.meli_category_id}/attributes"
        headers = {
            'Authorization': f'Bearer {instance.meli_access_token}'
        }

        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            attributes = response.json()
        except Exception as e:
            raise UserError(f"Error al consultar la API de atributos de MercadoLibre:\n{str(e)}")

        Attribute = self.env['vex.meli.attribute']
        Value = self.env['vex.meli.attribute.value']
        for attr in attributes:
            # Buscar si ya existe el atributo
            attribute = Attribute.search([
                ('meli_attribute_id', '=', attr.get('id')),
                ('meli_category_id', '=', self.id)
            ], limit=1)
            vals_attr = {
                'meli_attribute_name': attr.get('name'),
                'meli_attribute_required': attr.get('tags', {}).get('required', False),
                'meli_category_id': self.id,
            }
            if attribute:
                attribute.write(vals_attr)
            else:
                attribute = Attribute.create({
                    'meli_attribute_id': attr.get('id'),
                    **vals_attr
                })

            # Manejar valores del atributo
            for val in attr.get('values', []):
                value = Value.search([
                    ('meli_value_id', '=', val.get('id')),
                    ('attribute_id', '=', attribute.id)
                ], limit=1)
                vals_val = {
                    'meli_value_name': val.get('name'),
                    'attribute_id': attribute.id,
                }
                if value:
                    value.write(vals_val)
                else:
                    Value.create({
                        'meli_value_id': val.get('id'),
                        **vals_val
                    })
        return True

class MeliAttribute(models.Model):
    _name = 'vex.meli.attribute'
    _description = 'MercadoLibre Category Attribute'

    meli_category_id = fields.Many2one('product.category', string='Categoría MercadoLibre')
    meli_attribute_id = fields.Char(string='Attribute ID', required=True)
    meli_attribute_name = fields.Char(string='Attribute Name')
    meli_attribute_required = fields.Boolean(string='Required')
    value_ids = fields.One2many('vex.meli.attribute.value', 'attribute_id', string='Valores')

    def name_get(self):
        result = []
        for rec in self:
            name = f"{rec.meli_attribute_id or ''} - {rec.meli_attribute_name or ''}"
            result.append((rec.id, name))
        return result

class MeliAttributeValue(models.Model):
    _name = 'vex.meli.attribute.value'
    _description = 'MercadoLibre Category Attribute Value'
    _order = 'meli_value_name'

    meli_value_id = fields.Char(string='Value ID', required=True)
    meli_value_name = fields.Char(string='Value Name')
    attribute_id = fields.Many2one('vex.meli.attribute', string='Atributo')

    def name_get(self):
        result = []
        for rec in self:
            name = rec.meli_value_name or rec.meli_value_id
            if rec.attribute_id:
                # opcional: mostrar también el atributo al que pertenece
                name = f"{rec.attribute_id.meli_attribute_name}: {name}"
            result.append((rec.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('meli_value_name', operator, name), ('id', operator, name)]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()