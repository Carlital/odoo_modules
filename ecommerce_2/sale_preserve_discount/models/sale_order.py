from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    def _recompute_prices(self):
        lines_to_recompute = self._get_update_prices_lines()
        lines_to_recompute.invalidate_recordset(['pricelist_item_id'])
        lines_to_recompute.with_context(force_price_recomputation=True)._compute_price_unit()
        
        manual_discounts = {}
        for line in lines_to_recompute:
            if line.is_discount_manual:
                manual_discounts[line.id] = line.discount
        
        lines_to_recompute.discount = 0.0
        lines_to_recompute._compute_discount()
        
        for line in lines_to_recompute:
            if line.id in manual_discounts:
                line.discount = manual_discounts[line.id]
        
        self.show_update_pricelist = False
