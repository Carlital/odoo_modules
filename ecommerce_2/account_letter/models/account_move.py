# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class AccountInvoice(models.Model):
    _inherit = "account.move"

    def create_letters(self):
        if self:
            invoice_ids = self.env['account.move'].search([('id', 'in', self.ids)])
            currency_ids = invoice_ids.mapped('currency_id')
            if len(currency_ids) > 1:
                raise ValidationError(_('No se pueden generar letras de pagos con diferentes monedas'))
            partner_ids = invoice_ids.mapped('partner_id')
            if len(partner_ids) > 1:
                raise ValidationError(_('No se pueden generar letras de pagos con diferentes proveedores'))
        else:
            raise ValidationError(_('Debe seleccionar al menos una factura'))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.generate.letters',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'active_ids': self.ids}
        }
