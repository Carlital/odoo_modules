# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    discount_amount = fields.Float(string="Discount(AMT)", digits="Product Price", default=0.000)

    @api.depends('product_qty', 'price_unit', 'taxes_id','discount_amount')
    def _compute_amount(self):
        for line in self:
            tax_results = self.env['account.tax']._compute_taxes([line._convert_to_tax_base_line_dict()])
            totals = list(tax_results['totals'].values())[0]
            amount_untaxed = totals['amount_untaxed']
            amount_tax = totals['amount_tax']
            line.update({
                'price_subtotal': (line.price_unit * line.product_qty) - line.discount_amount,
                'price_tax': amount_tax,
                'price_total': amount_untaxed + amount_tax,
            })

    @api.onchange("discount")
    def _onchange_discount_percentage(self):
        for line in self:
            if float(line.discount) != 0:
                self.discount_amount = 0.0
                discount_amount = (line.price_unit * line.product_qty) * (float(line.discount) / 100.0)
                line.update({"discount_amount": discount_amount})
            if float(line.discount) == 0:
                discount_amount = 0.000
                line.update({"discount_amount": discount_amount})
            line._compute_amount()

    @api.onchange("discount_amount")
    def _onchange_discount_amount(self):
        for line in self:
            if line.discount_amount != 0:
                self.discount = 0.0
                if not line.price_unit:
                    raise UserError('Price Unit is Empty')
                if not line.product_qty:
                    raise UserError('Product Quantity is Empty')
                discount = ((self.product_qty * self.price_unit) - (
                        (self.product_qty * self.price_unit) - self.discount_amount)) / (
                                   self.product_qty * self.price_unit) * 100 or 0.0
                line.update({"discount": discount})
            if line.discount_amount == 0:
                discount = 0.0
                line.update({"discount": discount})
            line._compute_amount()

    def _convert_to_tax_base_line_dict(self):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """
        self.ensure_one()
        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.order_id.partner_id,
            currency=self.order_id.currency_id,
            product=self.product_id,
            taxes=self.taxes_id,
            price_unit=self.price_unit,
            discount=float(self.discount),
            quantity=self.product_qty,
            price_subtotal=self.price_subtotal,
        )

    def _prepare_account_move_line(self, move=False):
        self.ensure_one()
        aml_currency = move and move.currency_id or self.currency_id
        date = move and move.date or fields.Date.today()
        res = {
            'display_type': self.display_type or 'product',
            'name': '%s: %s' % (self.order_id.name, self.name),
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'discount': float(self.discount),
            'price_unit': self.currency_id._convert(self.price_unit, aml_currency, self.company_id, date, round=False),
            'tax_ids': [(6, 0, self.taxes_id.ids)],
            'purchase_line_id': self.id,
        }
        if self.analytic_distribution and not self.display_type:
            res['analytic_distribution'] = self.analytic_distribution
        return res
