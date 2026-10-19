import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'
    #Creación de campos
    surcharge_percentage = fields.Float(
        string="Porcentaje de Recargo",
        help="Define el porcentaje de recargo aplicado a los pagos con este método."
    )
    surcharge_product_id = fields.Many2one(
        'product.product',
        string="Producto de Recargo",
        domain=[('sale_ok', '=', True), ('type', '=', 'service')],
        help="Selecciona el producto/servicio al que se aplicará el recargo."
    )


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    def remove_surcharge_from_cart(self):
        """
        Elimina cualquier recargo en la orden si el estado es 'carrito' (estado borrador).
        """
        for order in self:
            surcharge_providers = order.transaction_ids.mapped('provider_id')

            for provider in surcharge_providers:
                surcharge_product = provider.surcharge_product_id
                if surcharge_product:
                    surcharge_lines = order.order_line.filtered(lambda line: line.product_id == surcharge_product)
                    if surcharge_lines:
                        surcharge_lines.unlink()
                        _logger.info("Líneas de recargo eliminadas del carrito para la orden %s", order.name)
                        
    @api.model
    def create(self, vals):
        order = super(SaleOrder, self).create(vals)
        order.remove_surcharge_from_cart()
        return order

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        self.remove_surcharge_from_cart()
        return res


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def create(self, values):
        # Crear la transacción
        transaction = super(PaymentTransaction, self).create(values)

        payment_provider = transaction.provider_id
        surcharge_percentage = payment_provider.surcharge_percentage
        surcharge_product = payment_provider.surcharge_product_id

        if surcharge_percentage and surcharge_product:
            # Calcular el recargo
            surcharge_amount = transaction.amount * (surcharge_percentage / 100)

            # Actualizar el monto de la transacción con el recargo
            transaction.amount += surcharge_amount

            if transaction.sale_order_ids:
                order = transaction.sale_order_ids[0]
                existing_surcharge_line = order.order_line.filtered(lambda line: line.product_id == surcharge_product)

                if existing_surcharge_line:
                    existing_surcharge_line.write({
                        'price_unit': surcharge_amount,
                        'product_uom_qty': 1,
                    })
                else:
                    order.order_line.create({
                        'order_id': order.id,
                        'product_id': surcharge_product.id,
                        'name': surcharge_product.name,
                        'product_uom_qty': 1,
                        'price_unit': surcharge_amount,
                        'tax_id': [(6, 0, surcharge_product.taxes_id.ids)],
                    })
        return transaction