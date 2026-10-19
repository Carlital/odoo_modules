from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    all_barcode_names = fields.Text(
        compute="_compute_all_barcode_names",
        string="All Barcodes",
        help="A list of all barcodes associated with this product, for PoS search.",
    )

    def _compute_all_barcode_names(self):
        for product in self:
            if product.barcode_ids:
                product.all_barcode_names = "\n".join(
                    product.barcode_ids.mapped("name"))
            else:
                product.all_barcode_names = ""

    @api.model
    def _loader_params_product_product(self):
        params = super()._loader_params_product_product()
        params["search_params"]["fields"].append("all_barcode_names")
        return params
