from odoo import models, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.onchange('state')
    def _onchange_state(self):
        """Previene el cambio de estado a borrador para facturas CPE publicadas."""
        for move in self:
            # Solo aplicar para facturas que son CPE y están en estado publicado
            if move.pe_is_cpe and move.state == 'posted':
                raise UserError(_(
                    'No está permitido cambiar a estado borrador las facturas que son '
                    'Comprobantes de Pago Electrónicos (CPE) y están en estado publicado.'
                ))

    def button_draft(self):
        """Sobrescribe el método de cambio a borrador para validar facturas CPE."""
        for move in self:
            if move.pe_is_cpe and move.state == 'posted':
                raise UserError(_(
                    'No está permitido cambiar a estado borrador las facturas que son '
                    'Comprobantes de Pago Electrónicos (CPE) y están en estado publicado.'
                ))
        return super(AccountMove, self).button_draft()
