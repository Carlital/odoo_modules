
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _write(self, vals):
        res = super()._write(vals)
        if vals.get('state', False) and self.state == 'paid':
            if self.origin:
                order = self.env['sale.order'].search(
                    [('name', '=', self.origin)])
                if not order:
                    order = self.env['purchase.order'].search(
                        [('name', '=', self.origin)])
                if order:
                    for pick in order.picking_ids:
                        pick.acs_state = 'pagado'
        return res
