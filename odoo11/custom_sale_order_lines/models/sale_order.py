import logging
from odoo import models, fields

# Configurar logger
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    order_line = fields.One2many(
        "sale.order.line",
        "order_id",
        string="Order Lines",
    )

    def toggle_show_order_lines(self):
        _logger.info("Executing toggle_show_order_lines method.")
        for record in self:
            # Log el estado inicial del campo
            _logger.info(
                "Sale Order %s (ID: %s) - Current Value of show_order_lines: %s",
                record.name, record.id, getattr(record, "show_order_lines", None),
            )
            record.show_order_lines = not record.show_order_lines
            # Log el nuevo estado del campo
            _logger.info(
                "Sale Order %s (ID: %s) - New Value of show_order_lines: %s",
                record.name, record.id, record.show_order_lines,
            )

            # Log la cantidad de líneas de pedido
            _logger.info(
                "Sale Order %s (ID: %s) has %d order lines.",
                record.name, record.id, len(record.order_line),
            )

            # Log detalles de las líneas de pedido (si existen)
            for line in record.order_line:
                _logger.info(
                    "Order Line: Product %s, Quantity: %s, Price: %s, Subtotal: %s",
                    line.product_id.name, line.product_uom_qty,
                    line.price_unit, line.price_subtotal,
                )

        # Forzar recarga de la vista y log
        _logger.info("Reloading the view after toggling.")
        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }
