
from odoo import fields, models


class BarcodeWizard(models.TransientModel):
    _name = "barcode.tag.wizard"
    _description = "Barcode Tag Wizard"

    qty = fields.Integer(
        'Cantidad de copias', default=1, required=True)

    def print_barcode(self):
        qty = self.qty
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')
        if not qty:
            qty = 1
        ids = []
        if active_model == 'purchase.order':
            purchase = self.env['purchase.order'].browse(active_id)
            for line in purchase.order_line:
                for i in range(qty):
                    ids.append(line.product_id.id)
        if active_model in ('product.template', 'product.product'):
            ids = [active_id for i in range(qty)]
        #docs = self.env[active_model].browse(ids)
        #docs.write({"qty_to_print":qty})
        return self.env.ref(
            'acs_product_labels_price.report_product_label').report_action(ids)

    def print_price(self):
        qty = self.qty
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')
        if not qty:
            qty = 1
        ids = []
        if active_model == 'purchase.order':
            purchase = self.env['purchase.order'].browse(active_id)
            for line in purchase.order_line:
                for i in range(qty):
                    ids.append(line.product_id.id)
        if active_model in ('product.template', 'product.product'):
            ids = [active_id for i in range(qty)]
        return self.env.ref(
            'acs_product_labels_price.report_product_label_price_acs').report_action(ids)
