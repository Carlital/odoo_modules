
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    penultimate_purchase_price = fields.Float(
        string='Precio de penúltima compra')

    def set_product_last_purchase(self, order_id=False):
        """ Get last purchase price, last purchase date and last supplier """
        PurchaseOrderLine = self.env['purchase.order.line']
        if not self.check_access_rights('write', raise_exception=False):
            return
        for product in self:
            date_order = False
            price_unit_uom = 0.0
            last_supplier = False
            penultimate_price = 0.0

            # Check if Order ID was passed, to speed up the search
            if order_id:
                lines = PurchaseOrderLine.search([
                    ('order_id', '=', order_id),
                    ('product_id', '=', product.id)], limit=1)
            else:
                lines = PurchaseOrderLine.search(
                    [('product_id', '=', product.id),
                     ('state', 'in', ['purchase', 'done'])]).sorted(
                    key=lambda l: l.order_id.date_order, reverse=True)

            if lines:
                # Get most recent Purchase Order Line
                last_line = lines[:1]

                date_order = last_line.order_id.date_order
                # Compute Price Unit in the Product base UoM
                price_unit_uom = last_line.product_uom._compute_price(
                    last_line.price_unit, product.product_tmpl_id.uom_id)
                last_supplier = last_line.order_id.partner_id

            # Assign values to record
            product.last_purchase_date = date_order
            product.last_purchase_price = price_unit_uom
            product.last_supplier_id = last_supplier

            purchase_lines = PurchaseOrderLine.search(
                [('product_id', '=', product.id),
                 ('state', 'in', ['purchase', 'done'])],
                order='id desc',
                limit=2)

            if len(purchase_lines) > 1:
                penultimate_price = purchase_lines[-1].product_uom._compute_price(
                    purchase_lines[-1].price_unit_pen, product.product_tmpl_id.uom_id)
            else:
                penultimate_price = 0.0

            product.penultimate_purchase_price = penultimate_price

            # Set related product template values
            product.product_tmpl_id.set_product_template_last_purchase(
                date_order, price_unit_uom, last_supplier)
            product.product_tmpl_id.set_product_template_penultimate_purchase(
                penultimate_price)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    penultimate_purchase_price = fields.Float(
        string='Precio de penúltima compra')

    equal_wholesale_import_price = fields.Boolean(
        'Igual Precio Mayorista e Importacion', default=True)

    def set_product_template_penultimate_purchase(self, price):
        self.penultimate_purchase_price = price

    def print_report_label_price(self, purchase_id, type=False):
        purchase = self.env['purchase.order'].browse(purchase_id)
        self = self.with_context(
            active_ids=[o.product_id.id for o in purchase.order_line])
        module = 'product'
        template = 'report_product_template_label'
        if type:
            module = 'acs_product_labels_price'
            template = 'report_product_template_label_price_acs'
        return self.env.ref(
            module + "." + template).report_action(self, data={})
