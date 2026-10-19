from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    total_purchases = fields.Integer(string='Número de Compras', compute='_compute_total_purchases')

    def _compute_total_purchases(self):
        for partner in self:
            start_date = self.env.context.get('start_date')
            end_date = self.env.context.get('end_date')
            if start_date and end_date:
                orders_in_period = partner.sale_order_ids.filtered(lambda o: o.date_order >= start_date and o.date_order <= end_date)
                partner.total_purchases = len(orders_in_period)
            else:
                partner.total_purchases = len(partner.sale_order_ids)

    
    repurchase_rate = fields.Float(string='Tasa de Recompra (%)', compute='_compute_repurchase_rate')

    def _compute_repurchase_rate(self):
        for partner in self:
            start_date = self.env.context.get('start_date')
            end_date = self.env.context.get('end_date')
            if start_date and end_date:
                orders_in_period = partner.sale_order_ids.filtered(lambda o: o.date_order >= start_date and o.date_order <= end_date)
                total_purchases = len(orders_in_period)
                if total_purchases > 1:
                    partner.repurchase_rate = ((total_purchases - 1) / total_purchases) * 100
                else:
                    partner.repurchase_rate = 0
            else:
                partner.repurchase_rate = 0
