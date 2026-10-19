
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_brand_default(self):
        return self.env.user.brand_id.id

    brand_comercial_id = fields.Many2one(
        'brand.comercial.tours',
        'Marca comercial',
        default=_get_brand_default
    )
    custom_template_mail_sale_id = fields.Many2one(
        'mail.template',
        string='Plantilla de correo para Ventas',
        related='brand_comercial_id.custom_template_mail_sale_id'
    )
    hotel_id = fields.Many2many(
        'hotel.tour',
        'sale_hotel_rel_acs',
        'hotel_id',
        'sale_id',
        string='Hotel Principal'
    )
    hotel_detail = fields.Many2many(
        'hotel.tour',
        'sale_hotel_detail_rel_acs',
        'hotel_id',
        'sale_id',
        string='Hotel Secundario'
    )