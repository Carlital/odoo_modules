from odoo import models, fields

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    selected_product_id = fields.Many2one('product.product', string='Selected Product')
    selected_product_code = fields.Char(related='selected_product_id.default_code', string='Selected Product Code', readonly=True)
    color = fields.Char(string='Color')
    price = fields.Float(string='Price')
    promotion = fields.Char(string='Promotion')
    payment_option = fields.Char(string='Payment Option')
    monthly_payment = fields.Float(string='Monthly Payment')
    test_drive = fields.Boolean(string='Test Drive')
    test_drive_date = fields.Date(string='Test Drive Date')
    test_drive_time = fields.Float(string='Test Drive Time')
    email_from = fields.Char(string='Email', help='Email address of the contact')