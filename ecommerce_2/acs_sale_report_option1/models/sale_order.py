from odoo import models

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # No es necesario redefinir los campos si ya existen,
    # solo si necesitas lógica extra, puedes agregar métodos aquí.
    # Por ejemplo, para mostrar el guión si el valor es 0 o vacío:

    def get_or_dash(self, value):
        if not value or value == 0.0:
            return '-'
        return value