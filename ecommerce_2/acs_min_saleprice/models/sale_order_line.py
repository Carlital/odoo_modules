# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.constrains('product_id', 'price_unit')
    def _check_min_sale_price(self):
        """
        Verifica que el precio de venta no sea inferior al precio mínimo configurado,
        considerando también las reglas de listas de precios.
        """
        # Obtenemos la moneda de la compañía para comparaciones
        company_currency = self.env.company.currency_id

        for line in self:
            # Si no hay producto o el precio es cero, no hay nada que validar
            if not line.product_id or float_is_zero(line.price_unit, precision_digits=company_currency.decimal_places):
                continue

            product = line.product_id
            user_min_price = product.min_saleprice

            # Si no se ha definido un precio mínimo en el producto, no validamos
            if not user_min_price or user_min_price <= 0:
                continue

            # --- Lógica de la Lista de Precios Contextual ---
            # Usamos la lógica nativa de Odoo para obtener el precio de la tarifa
            # para la cantidad específica en esta línea de pedido.
            pricelist = line.order_id.pricelist_id
            pricelist_price = pricelist._get_product_price(
                product, line.product_uom_qty, uom=line.product_uom)

            # Si la tarifa devuelve un precio, lo usamos. Si no, consideramos el precio
            # de venta base del producto como referencia.
            # Esto es importante porque si no hay regla de tarifa, no debemos permitir
            # vender por debajo del min_saleprice.
            # Si la tarifa SÍ da un precio, ese precio tiene prioridad si es menor.
            if pricelist_price < user_min_price:
                # La tarifa permite un precio más bajo que el mínimo manual (ej. por volumen)
                effective_min_price = pricelist_price
            else:
                # El mínimo manual es el que rige
                effective_min_price = user_min_price

            # Convertimos el precio unitario de la línea a la moneda de la compañía
            # para una comparación precisa, en caso de que el pedido use otra moneda.
            price_unit_in_company_currency = line.currency_id._convert(
                line.price_unit,
                company_currency,
                line.company_id,
                line.order_id.date_order or fields.Date.today()
            )

            # --- Validación Final ---
            # Comparamos con una pequeña tolerancia para evitar problemas de flotantes
            if price_unit_in_company_currency < effective_min_price and not float_is_zero(effective_min_price - price_unit_in_company_currency, precision_digits=company_currency.decimal_places):
                raise ValidationError(_(
                    "El precio de venta para el producto '%(product)s' no puede ser inferior a %(price)s %(currency)s para la cantidad solicitada.\n"
                    "El precio mínimo permitido para esta operación es %(price)s.",
                    product=product.display_name,
                    price=f"{effective_min_price:,.2f}",
                    currency=company_currency.symbol
                ))
