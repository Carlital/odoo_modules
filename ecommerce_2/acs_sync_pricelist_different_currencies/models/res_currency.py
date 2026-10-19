from odoo import models, api


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    def write(self, vals):
        result = super().write(vals)
        # Si se actualizó alguna tasa de cambio
        if 'rate' in vals or 'rate_ids' in vals:
            self.env['product.pricelist']._update_on_currency_rate_change()
        return result


class ResCurrencyRate(models.Model):
    _inherit = 'res.currency.rate'

    def write(self, vals):
        result = super().write(vals)
        # Si se actualizó la tasa
        if 'rate' in vals:
            self.env['product.pricelist']._update_on_currency_rate_change()
        return result

    @api.model_create_multi
    def create(self, vals_list):
        rates = super().create(vals_list)
        self.env['product.pricelist']._update_on_currency_rate_change()
        return rates
