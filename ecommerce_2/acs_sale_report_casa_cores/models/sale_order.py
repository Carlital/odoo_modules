from odoo import models, fields
import pytz

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    lugar_entrega = fields.Char(string='Lugar de entrega', default='')

    def get_local_date_str(self):
        if not self.date_order:
            return ""
        user_tz = pytz.timezone(self.env.user.tz or 'UTC')
        return self.date_order.astimezone(user_tz).strftime('%d/%m/%Y')