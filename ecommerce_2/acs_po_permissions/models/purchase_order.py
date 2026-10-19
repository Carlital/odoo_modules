from odoo import models, fields, api
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        for record in self:
            if record.env.user.acs_po_no_confirm:
                raise UserError(
                    "No tienes permisos para confirmar esta orden de compra.")
            else:
                super(PurchaseOrder, record).button_confirm()
        return True
