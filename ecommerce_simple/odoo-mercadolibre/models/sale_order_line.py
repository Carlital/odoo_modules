from odoo import models, fields

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Campo relacionado a la categoría del producto
    product_categ_id = fields.Many2one(related='product_id.categ_id', store=True, string="Product Category")
    order_date = fields.Datetime(related='order_id.date_order', store=True, string="Order Date")
    product_brand = fields.Char(
        string="Brand",
        compute="_compute_product_brand",
        store=True
    )

    def _compute_product_brand(self):
        for line in self:
            if line.product_id:
                # Acceder al template del producto y luego obtener las líneas de atributos
                attribute_line = line.product_id.product_tmpl_id.attribute_line_ids.filtered(
                    lambda l: l.attribute_id.name == 'Marca')
                if attribute_line:
                    # Si se encuentra el atributo "Marca", tomar el valor
                    line.product_brand = ', '.join(attribute_line.mapped('value_ids.name'))
                    #line.product_brand = attribute_line.mapped('value_ids.name')[0] if attribute_line.mapped('value_ids.name') else False
                else:
                    line.product_brand = False
            else:
                line.product_brand = False

