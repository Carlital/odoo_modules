from odoo import api, fields, models, exceptions

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    preferred_method = fields.Boolean(string='Preferente', default=False)

    @api.constrains('preferred_method')
    def _check_unique_preferred_method(self):
        for record in self:
            if record.preferred_method:
                # Buscamos otros diarios con preferred_method = True
                existing_preferred = self.search_count([
                    ('id', '!=', record.id),
                    ('preferred_method', '=', True)
                ])
                if existing_preferred:
                    raise exceptions.ValidationError(
                        "Ya existe un diario marcado como 'Preferente'. Por favor, desactiva el campo en el diario '%s' antes de activarlo aquí." % 
                        self.search([('preferred_method', '=', True), ('id', '!=', record.id)], limit=1).name
                    )