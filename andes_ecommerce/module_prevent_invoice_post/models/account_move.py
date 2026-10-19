from odoo import models, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self, *args, **kwargs):
        for move in self:
            if move.move_type in ["out_invoice", "out_refund"]:
                if self.env.context.get("pos_autoinvoice"):
                    raise UserError(_("No se puede confirmar esta factura generada desde el Punto de Venta. Contacte con el administrador."))
                raise UserError(_("No se puede confirmar esta factura. Contacte con el administrador."))
        
        return super(AccountMove, self).action_post(*args, **kwargs)

