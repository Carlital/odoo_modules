
from odoo import api, fields, models


class Picking(models.Model):
    _inherit = "stock.picking"

    acs_state = fields.Selection(
        [('pagado', 'Pagado'),
         ('observado', 'Observado'),
         ('recibido', 'Recibido'),
         ('cancelado', 'Cancelado')],
        string='Estado', track_visibility='onchange', readonly=True)

    def action_done(self):
        res = super().action_done()
        for pick in self:
            pick.acs_state = 'recibido'
        return res

    def action_obs(self):
        return self.write({'acs_state': 'observado'})

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(Picking, self).fields_get(allfields, attributes)
        if self.env.user.has_group('acs_stock.group_allow_acs_state'):
            if 'acs_state' in res:
                res['acs_state']['readonly'] = False
        return res
    
    def action_cancel(self):
        res = super().action_cancel()
        for pick in self:
            pick.acs_state = 'cancelado'
        return res