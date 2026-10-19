from odoo import models, _ 
from odoo.exceptions import UserError

class PosOrder(models.Model):
    _inherit = "pos.order"

    def _create_invoice(self, *args, **kwargs):
        invoices = super(PosOrder, self)._create_invoice(*args, **kwargs)
        
        for invoice in invoices:
            if invoice.move_type == "out_invoice":
                raise UserError(_("No se puede confirmar la factura generada desde el Punto de Venta. Contacte con el administrador."))
        
        return invoices
