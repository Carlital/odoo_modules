
from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'stock.picking'

    def _get_brand_default(self):
        return self.env.user.brand_id.id

    brand_comercial_id = fields.Many2one(
        'brand.comercial.tours',
        'Marca comercial',
        default=_get_brand_default
    )


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('origin',False):
                sale_id = self.env['sale.order'].search([('name','=',vals.get('origin',False))])
                if sale_id:
                    vals.update({'brand_comercial_id':sale_id.brand_comercial_id.id})
        created_records = super().create(vals_list)
        return created_records

    def write(self, values):
        result = super().write(values)
        return result