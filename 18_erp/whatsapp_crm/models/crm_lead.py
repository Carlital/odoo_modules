from odoo import models, fields

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    selected_product_id = fields.Many2one('product.product', string='Selected Product')
    selected_product_code = fields.Char(related='selected_product_id.default_code', string='Selected Product Code', readonly=True)
    price = fields.Float(string='Price')
