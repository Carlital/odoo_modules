from odoo import api, fields, models, exceptions

class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    inmediate_pay = fields.Boolean(string='Pago Inmediato', default=False)

    @api.constrains('inmediate_pay')
    def _check_unique_inmediate_pay(self):
        for record in self:
            if record.inmediate_pay:
                # Buscamos otros términos de pago con inmediate_pay = True
                existing_inmediate = self.search_count([
                    ('id', '!=', record.id),
                    ('inmediate_pay', '=', True)
                ])
                if existing_inmediate:
                    raise exceptions.ValidationError(
                        "Ya existe un término de pago marcado como 'Pago Inmediato'. Por favor, desactiva el campo en el término '%s' antes de activarlo aquí." % 
                        self.search([('inmediate_pay', '=', True), ('id', '!=', record.id)], limit=1).name
                    )