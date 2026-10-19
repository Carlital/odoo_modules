from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    is_discount_manual = fields.Boolean(string="Manual Discount", default=False)
    last_known_discount = fields.Float(string="Last Known Discount", default=0.0)
    
    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_discount(self):
        for line in self:
            if line.is_discount_manual:
                continue
                
            super(SaleOrderLine, line)._compute_discount()
    
    @api.onchange('discount')
    def _onchange_discount(self):
        if self.discount != self.last_known_discount and not self._context.get('discount_from_qty_change'):
            self.is_discount_manual = True
        
        self.last_known_discount = self.discount
    
    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        self.env.context = dict(self.env.context, discount_from_qty_change=True)
        return {}
    
    def write(self, vals):
        for line in self:
            if 'discount' in vals and 'product_uom_qty' not in vals:
                vals['is_discount_manual'] = True
                vals['last_known_discount'] = vals['discount']
        
        return super(SaleOrderLine, self).write(vals)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'discount' in vals and vals.get('discount', 0.0) != 0.0:
                vals['is_discount_manual'] = True
                vals['last_known_discount'] = vals.get('discount', 0.0)
        
        return super(SaleOrderLine, self).create(vals_list)
