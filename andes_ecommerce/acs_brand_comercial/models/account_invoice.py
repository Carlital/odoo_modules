
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'
    def _get_brand_default(self):
        return self.env.user.brand_id.id
    brand_comercial_id = fields.Many2one(
        'brand.comercial.tours',
        'Marca comercial',
        default=_get_brand_default
    )
    custom_template_mail_invoice_id = fields.Many2one(
        'mail.template',
        string='Plantilla de correo para Facturación',
        related='brand_comercial_id.custom_template_mail_invoice_id'
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        'Orden de venta',
        compute="_compute_sale_order"
    )
    hotel_id = fields.Many2many(
        'hotel.tour',
        'account_hotel_rel_acs',
        'hotel_id',
        'account_id',
        string='Hotel Principal'
    )
    hotel_detail = fields.Many2many(
        'hotel.tour',
        'account_hotel_detail_rel_acs',
        'hotel_id',
        'account_id',
        string='Hotel Secundario'
    )

    def _compute_sale_order(self):
        for rec in self:
            if rec.invoice_origin:
                sale = self.env['sale.order'].search(
                    [('name', '=', rec.invoice_origin)])
                rec.sale_order_id = sale