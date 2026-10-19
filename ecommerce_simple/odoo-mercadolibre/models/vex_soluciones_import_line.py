from odoo import fields, models, api

class VexSolucionesImportLine(models.Model):
    _name="vex.import_line"
    _order = "create_date desc"
    
    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')
    description = fields.Char('Description')
    stock_import = fields.Boolean('Stock import')
    images_import = fields.Boolean('Images import')
    status = fields.Selection([
        ('done', 'Done'),
        ('pending', 'Pending'),
        ('error', 'Error'),('obs', 'Observed')
    ], string='Status')

    instance_id = fields.Many2one('vex.instance', string='Instance id')

    action = fields.Selection([
        ('product', 'Product'),
        ('order', 'Order')
    ], string='Action')
    checks_indicator = fields.Char('Counter')
    result = fields.Char('Result')

    store_type = fields.Selection([
        ('mercadolibre', 'Mercado Libre'),
        ('walmart', 'Walmart')
    ], string="Store Type", required=True, default='mercadolibre')


    def _prepare_product_values(self, item_data, category_id, image_1920, attribute_value_tuples, sku_id, stock_location_obj, ml_reference, marketplace_fee, import_line_id):
        Tag = self.env['product.meli.tag']
        Channel = self.env['product.meli.channel']
        Picture = self.env['product.template.meli.image']
        Attribute = self.env['product.template.meli.attribute']
        Variation = self.env['product.template.meli.variation']
        Marketplace = self.env['product.marketplace']

        # Tags
        tag_ids = []
        for tag in item_data.get('tags', []):
            tag_rec = Tag.search([('name', '=', tag)], limit=1)
            if not tag_rec:
                tag_rec = Tag.create({'name': tag})
            tag_ids.append(tag_rec.id)

        # Channels
        channel_ids = []
        for channel in item_data.get('channels', []):
            ch_rec = Channel.search([('name', '=', channel)], limit=1)
            if not ch_rec:
                ch_rec = Channel.create({'name': channel})
            channel_ids.append(ch_rec.id)

        # Pictures
        picture_vals = []
        for pic in item_data.get('pictures', []):
            picture_vals.append((0, 0, {
                'url': pic.get('secure_url'),
                'product_tmpl_id': False  # se asigna automáticamente
            }))

        # Attributes
        attribute_vals = []
        for attr in item_data.get('attributes', []):
            value_names = [v.get('name') for v in attr.get('values', []) if v.get('name')]
            attribute_vals.append((0, 0, {
                'meli_attribute_id': attr.get('id'),
                'meli_attribute_name': attr.get('name'),
                'meli_value_id': attr.get('value_id'),
                'meli_value_name': ', '.join(value_names),
            }))

        # Variations
        variation_vals = []
        for var in item_data.get('variations', []):
            attribute_combinations = var.get('attribute_combinations', [])
            attrs = ', '.join([ac.get('value_name') for ac in attribute_combinations if ac.get('value_name')])
            variation_vals.append((0, 0, {
                'meli_variation_id': var.get('id'),
                'meli_price': var.get('price'),
                'meli_available_quantity': var.get('available_quantity'),
                'meli_sold_quantity': var.get('sold_quantity'),
                'meli_attribute_combination': attrs,
            }))

        # Marketplace
        marketplace = Marketplace.search([('name', '=', 'mercadolibre')], limit=1)
        if not marketplace:
            marketplace = Marketplace.create({'name': 'mercadolibre'})

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
            'upc': next((attr['value_name'] for attr in item_data.get('attributes', []) if attr['id'] == 'GTIN'), None),
            'store_type': 'mercadolibre',
            'market_fee': marketplace_fee,

            # Relaciones
            'meli_tag_ids': [(6, 0, tag_ids)],
            'meli_channel_ids': [(6, 0, channel_ids)],
            'marketplace_ids': [(4, marketplace.id)],
            'meli_pictures_ids': picture_vals,
            'meli_attribute_ids': attribute_vals,
            'meli_variation_ids': variation_vals,
        }